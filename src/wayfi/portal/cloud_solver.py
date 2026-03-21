"""Cloud API fallback solver using Claude or OpenAI via iPhone hotspot."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass

from wayfi.portal.llm_solver import LLMSolveResult, clean_portal_html, SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

logger = logging.getLogger(__name__)


@dataclass
class CloudConfig:
    provider: str = "claude"  # "claude" or "openai"
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    timeout: int = 15


async def _detect_hotspot_interface() -> str | None:
    """Detect iPhone USB tethering interface (en* or usb*)."""
    proc = await asyncio.create_subprocess_exec(
        "ip", "route", "show", "default",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace")
    # Look for interfaces that aren't our WiFi interfaces
    for line in output.splitlines():
        parts = line.split()
        for i, part in enumerate(parts):
            if part == "dev" and i + 1 < len(parts):
                iface = parts[i + 1]
                if iface.startswith(("en", "usb", "eth")):
                    return iface
    return None


class CloudSolver:
    """Cloud API fallback for portal solving when local LLM fails.

    Routes API calls through iPhone USB tethering interface when available,
    since the main WiFi is behind the unsolved captive portal.
    """

    def __init__(self, config: CloudConfig | None = None) -> None:
        self.config = config or CloudConfig()

    async def solve(self, portal_html: str, portal_url: str = "") -> LLMSolveResult:
        """Try cloud providers in order: Claude first, then OpenAI."""
        cleaned = clean_portal_html(portal_html)
        if not cleaned.strip():
            return LLMSolveResult(success=False, error="No form content found")

        # Try Claude first
        if self.config.claude_api_key:
            result = await self._solve_claude(cleaned, portal_url)
            if result.success:
                return result
            logger.warning("Claude API failed: %s — trying OpenAI", result.error)

        # Fall back to OpenAI
        if self.config.openai_api_key:
            result = await self._solve_openai(cleaned, portal_url)
            if result.success:
                return result
            logger.warning("OpenAI API failed: %s", result.error)

        return LLMSolveResult(
            success=False,
            error="All cloud providers failed or not configured",
        )

    async def _solve_claude(self, cleaned_html: str, portal_url: str) -> LLMSolveResult:
        """Call Claude API (Anthropic SDK)."""
        try:
            import anthropic
        except ImportError:
            return LLMSolveResult(success=False, error="anthropic package not installed")

        user_content = cleaned_html
        if portal_url:
            user_content = f"Portal URL: {portal_url}\n\n{cleaned_html}"

        try:
            client = anthropic.AsyncAnthropic(api_key=self.config.claude_api_key)
            response = await asyncio.wait_for(
                client.messages.create(
                    model=self.config.claude_model,
                    max_tokens=512,
                    system=SYSTEM_PROMPT,
                    messages=_build_messages(user_content),
                ),
                timeout=self.config.timeout,
            )
            content = response.content[0].text
            return _parse_json_response(content)

        except asyncio.TimeoutError:
            return LLMSolveResult(success=False, error="Claude API timeout")
        except Exception as e:
            return LLMSolveResult(success=False, error=f"Claude API error: {e}")

    async def _solve_openai(self, cleaned_html: str, portal_url: str) -> LLMSolveResult:
        """Call OpenAI API."""
        try:
            import openai
        except ImportError:
            return LLMSolveResult(success=False, error="openai package not installed")

        user_content = cleaned_html
        if portal_url:
            user_content = f"Portal URL: {portal_url}\n\n{cleaned_html}"

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(FEW_SHOT_EXAMPLES)
        messages.append({"role": "user", "content": user_content})

        try:
            client = openai.AsyncOpenAI(api_key=self.config.openai_api_key)
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=512,
                    response_format={"type": "json_object"},
                ),
                timeout=self.config.timeout,
            )
            content = response.choices[0].message.content
            return _parse_json_response(content)

        except asyncio.TimeoutError:
            return LLMSolveResult(success=False, error="OpenAI API timeout")
        except Exception as e:
            return LLMSolveResult(success=False, error=f"OpenAI API error: {e}")


def _build_messages(user_content: str) -> list[dict]:
    """Build message list for Claude API (alternating user/assistant)."""
    messages = []
    for example in FEW_SHOT_EXAMPLES:
        messages.append({
            "role": example["role"],
            "content": example["content"],
        })
    messages.append({"role": "user", "content": user_content})
    return messages


def _parse_json_response(content: str) -> LLMSolveResult:
    """Parse JSON from cloud API response."""
    content = content.strip()

    # Handle markdown code blocks
    json_match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        return LLMSolveResult(
            success=False, raw_response=content[:500],
            error=f"Invalid JSON: {e}",
        )

    fields = parsed.get("fields", {})
    if not isinstance(fields, dict):
        fields = {}

    checkboxes = parsed.get("checkboxes", [])
    if not isinstance(checkboxes, list):
        checkboxes = []

    return LLMSolveResult(
        success=True,
        action_url=parsed.get("action_url", ""),
        method=parsed.get("method", "POST"),
        fields=fields,
        checkboxes=checkboxes,
        raw_response=content[:500],
    )
