"""Heuristic pattern-matching engine for captive portal solving."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PATTERNS_DIR = Path(__file__).parent / "patterns"


@dataclass
class SolveStrategy:
    vendor: str
    pattern_name: str
    action_url_pattern: str
    method: str  # GET or POST
    fields: dict[str, str]  # field_name -> value (may contain {vault.xxx} tokens)
    checkboxes: list[str] = field(default_factory=list)


@dataclass
class HeuristicMatch:
    vendor: str
    pattern_name: str
    strategy: SolveStrategy
    confidence: float  # 0.0 - 1.0
    match_time_ms: float = 0.0


@dataclass
class CompiledPattern:
    name: str
    vendor: str
    url_patterns: list[re.Pattern]
    html_signals: list[re.Pattern]
    strategy: dict  # raw solve_strategy from YAML
    min_signals: int = 1  # how many signals must match


class HeuristicEngine:
    """Pattern-based captive portal solver. Loads YAML patterns at boot,
    compiles regex once, and matches against portal URL + HTML."""

    def __init__(self, patterns_dir: Path | None = None) -> None:
        self.patterns_dir = patterns_dir or PATTERNS_DIR
        self._patterns: list[CompiledPattern] = []
        self._loaded = False

    def load_patterns(self) -> int:
        """Load and compile all YAML pattern files. Call once at boot."""
        self._patterns = []
        if not self.patterns_dir.exists():
            logger.warning("Patterns directory not found: %s", self.patterns_dir)
            return 0

        for yaml_file in sorted(self.patterns_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(yaml_file.read_text())
                if not data:
                    continue
                compiled = self._compile_pattern(data)
                self._patterns.append(compiled)
            except Exception as e:
                logger.error("Failed to load pattern %s: %s", yaml_file.name, e)

        self._loaded = True
        logger.info("Loaded %d portal patterns", len(self._patterns))
        return len(self._patterns)

    def _compile_pattern(self, data: dict) -> CompiledPattern:
        """Compile a single pattern definition into regex objects."""
        detection = data.get("detection_signals", {})

        url_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in detection.get("url_patterns", [])
        ]
        html_signals = [
            re.compile(p, re.IGNORECASE | re.DOTALL)
            for p in detection.get("html_signals", [])
        ]

        return CompiledPattern(
            name=data.get("name", "unknown"),
            vendor=data.get("vendor", "unknown"),
            url_patterns=url_patterns,
            html_signals=html_signals,
            strategy=data.get("solve_strategy", {}),
            min_signals=detection.get("min_signals", 1),
        )

    def match(
        self,
        portal_html: str,
        portal_url: str,
        vault_values: dict[str, str] | None = None,
    ) -> HeuristicMatch | None:
        """Try to match portal against all loaded patterns.

        Returns the best match or None. Target: sub-50ms.
        """
        if not self._loaded:
            self.load_patterns()

        start = time.monotonic()
        best_match: HeuristicMatch | None = None
        best_score = 0

        for pattern in self._patterns:
            score = self._score_pattern(pattern, portal_html, portal_url)
            if score > best_score and score >= pattern.min_signals:
                strategy = self._build_strategy(pattern, vault_values or {})
                best_match = HeuristicMatch(
                    vendor=pattern.vendor,
                    pattern_name=pattern.name,
                    strategy=strategy,
                    confidence=min(1.0, score / max(
                        len(pattern.url_patterns) + len(pattern.html_signals), 1
                    )),
                )
                best_score = score

        elapsed_ms = (time.monotonic() - start) * 1000
        if best_match:
            best_match.match_time_ms = elapsed_ms
            logger.info(
                "Heuristic match: %s (%s) confidence=%.2f in %.1fms",
                best_match.pattern_name,
                best_match.vendor,
                best_match.confidence,
                elapsed_ms,
            )
        else:
            logger.info("No heuristic match found (%.1fms)", elapsed_ms)

        return best_match

    def _score_pattern(
        self, pattern: CompiledPattern, html: str, url: str
    ) -> int:
        """Count how many detection signals match."""
        score = 0
        for regex in pattern.url_patterns:
            if regex.search(url):
                score += 1
        for regex in pattern.html_signals:
            if regex.search(html):
                score += 1
        return score

    def _build_strategy(
        self, pattern: CompiledPattern, vault_values: dict[str, str]
    ) -> SolveStrategy:
        """Build a SolveStrategy from pattern data, interpolating vault values."""
        strat = pattern.strategy
        fields = {}
        for name, value in strat.get("fields", {}).items():
            fields[name] = self._interpolate(str(value), vault_values)

        return SolveStrategy(
            vendor=pattern.vendor,
            pattern_name=pattern.name,
            action_url_pattern=strat.get("action_url_pattern", ""),
            method=strat.get("method", "POST"),
            fields=fields,
            checkboxes=strat.get("checkboxes", []),
        )

    def _interpolate(self, template: str, vault_values: dict[str, str]) -> str:
        """Replace {vault.xxx} tokens with actual values."""
        def replacer(m: re.Match) -> str:
            key = m.group(1)
            return vault_values.get(key, m.group(0))

        return re.sub(r"\{vault\.(\w+)\}", replacer, template)
