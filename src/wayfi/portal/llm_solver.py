"""Local LLM portal solver via llama.cpp OpenAI-compatible API."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import aiohttp
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)

# GBNF grammar for constrained JSON output
PORTAL_JSON_GRAMMAR = r'''
root ::= "{" ws "\"action_url\"" ws ":" ws string "," ws "\"method\"" ws ":" ws method "," ws "\"fields\"" ws ":" ws fields "," ws "\"checkboxes\"" ws ":" ws checkboxes "}" ws
method ::= "\"GET\"" | "\"POST\""
fields ::= "{" ws (field ("," ws field)*)? ws "}"
field ::= string ws ":" ws string
checkboxes ::= "[" ws (string ("," ws string)*)? ws "]"
string ::= "\"" ([^"\\] | "\\" .)* "\""
ws ::= [ \t\n]*
'''

SYSTEM_PROMPT = """You are a captive portal form analyzer. Given HTML from a WiFi login page, extract the form submission details as JSON.

Return ONLY a JSON object with these fields:
- action_url: the form's action URL (or empty string if not found)
- method: "GET" or "POST"
- fields: object mapping field names to suggested values. For fields that need user credentials, use these tokens:
  - {vault.room_number} for room number fields
  - {vault.last_name} for last name fields
  - {vault.first_name} for first name fields
  - {vault.email} for email fields
  - {vault.email_throwaway} for throwaway email fields
  - {vault.phone} for phone fields
  - {vault.loyalty_hilton}, {vault.loyalty_marriott}, {vault.loyalty_ihg} for loyalty numbers
  - For hidden fields, use their existing value attribute
  - For checkbox/TOS fields, use "on"
- checkboxes: array of checkbox field names that should be checked"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": '<form action="/login" method="POST"><input type="hidden" name="token" value="abc123"/><input name="room" placeholder="Room Number"/><input name="lastName" placeholder="Last Name"/><input type="checkbox" name="tos"/><button type="submit">Connect</button></form>',
    },
    {
        "role": "assistant",
        "content": '{"action_url": "/login", "method": "POST", "fields": {"token": "abc123", "room": "{vault.room_number}", "lastName": "{vault.last_name}", "tos": "on"}, "checkboxes": ["tos"]}',
    },
    {
        "role": "user",
        "content": '<form action="/guest/auth" method="POST"><input name="email" type="email" placeholder="Email Address"/><input name="name" placeholder="Full Name"/><input type="checkbox" name="terms" id="terms"/><input type="submit" value="Accept & Connect"/></form>',
    },
    {
        "role": "assistant",
        "content": '{"action_url": "/guest/auth", "method": "POST", "fields": {"email": "{vault.email_throwaway}", "name": "{vault.first_name} {vault.last_name}", "terms": "on"}, "checkboxes": ["terms"]}',
    },
    {
        "role": "user",
        "content": '<form method="POST"><button type="submit" class="btn-connect">Accept & Connect</button><input type="hidden" name="dst" value="http://google.com"/><input type="hidden" name="popup" value="true"/></form>',
    },
    {
        "role": "assistant",
        "content": '{"action_url": "", "method": "POST", "fields": {"dst": "http://google.com", "popup": "true"}, "checkboxes": []}',
    },
]


@dataclass
class LLMSolveResult:
    success: bool
    action_url: str = ""
    method: str = "POST"
    fields: dict[str, str] | None = None
    checkboxes: list[str] | None = None
    raw_response: str = ""
    error: str = ""


def clean_portal_html(html: str) -> str:
    """Strip non-essential HTML while preserving form structure.

    Keeps: form, input, select, button, label, a, option, textarea, noscript
    Strips: script, style, img, svg, comments, meta, link, head
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles, images, SVGs, comments
    for tag in soup.find_all(["script", "style", "img", "svg", "meta", "link", "head"]):
        tag.decompose()
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    # Keep only form-relevant tags
    keep_tags = {"form", "input", "select", "button", "label", "a", "option",
                 "textarea", "noscript", "fieldset", "legend", "div", "span", "p", "h1", "h2", "h3"}

    # Get text content, focusing on forms
    forms = soup.find_all("form")
    if forms:
        # Return just the form HTML
        parts = []
        for form in forms:
            parts.append(str(form))
        return "\n".join(parts)

    # No form tags found — return cleaned full HTML (some portals build forms with JS)
    return soup.get_text(separator="\n", strip=True)[:4000]


class LLMSolver:
    """Solve captive portals using a local LLM via llama.cpp's OpenAI-compatible API."""

    def __init__(
        self,
        endpoint: str = "http://localhost:8080",
        model: str = "llama-3.1-8b",
        timeout: int = 30,
        use_grammar: bool = True,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.use_grammar = use_grammar

    async def solve(self, portal_html: str, portal_url: str = "") -> LLMSolveResult:
        """Send cleaned portal HTML to the LLM and parse the JSON response."""
        cleaned = clean_portal_html(portal_html)
        if not cleaned.strip():
            return LLMSolveResult(success=False, error="No form content found in HTML")

        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(FEW_SHOT_EXAMPLES)

        user_content = cleaned
        if portal_url:
            user_content = f"Portal URL: {portal_url}\n\n{cleaned}"
        messages.append({"role": "user", "content": user_content})

        # Build request body
        body: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 512,
            "stream": False,
        }
        if self.use_grammar:
            body["grammar"] = PORTAL_JSON_GRAMMAR

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.endpoint}/v1/chat/completions",
                    json=body,
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return LLMSolveResult(
                            success=False,
                            error=f"LLM API returned {resp.status}: {text[:200]}",
                        )
                    data = await resp.json()

        except Exception as e:
            logger.error("LLM API call failed: %s", e)
            return LLMSolveResult(success=False, error=str(e))

        # Parse response
        try:
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)
        except (KeyError, IndexError) as e:
            return LLMSolveResult(
                success=False,
                raw_response=json.dumps(data)[:500],
                error=f"Unexpected response structure: {e}",
            )

    def _parse_response(self, content: str) -> LLMSolveResult:
        """Parse the LLM's JSON response into a structured result."""
        # Try to extract JSON from the response
        content = content.strip()

        # Handle markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            return LLMSolveResult(
                success=False,
                raw_response=content[:500],
                error=f"Invalid JSON from LLM: {e}",
            )

        if not isinstance(parsed, dict):
            return LLMSolveResult(
                success=False, raw_response=content[:500],
                error="LLM returned non-object JSON",
            )

        fields = parsed.get("fields")
        if not isinstance(fields, dict):
            fields = {}

        checkboxes = parsed.get("checkboxes")
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

    async def health_check(self) -> bool:
        """Check if the LLM server is responding."""
        timeout = aiohttp.ClientTimeout(total=5)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoint}/health") as resp:
                    return resp.status == 200
        except Exception:
            return False
