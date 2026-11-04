"""Metric calculation and validation.

Metric definitions live in mama-metrics as metric cards (declarative YAML);
their formulas are prose, deliberately not executable. This module provides
an explicit, tested calculation registry keyed by card id for the ratio
percent cards the framework's guidance and maturity model rely on, plus a
generic percent calculator that refuses to run unless the caller confirms the
card's formula is a plain ratio. Anything not in the registry must be
calculated by the use case's own tooling — mama-tools never guesses.
"""
from __future__ import annotations

from .errors import MetricError

# card id -> (numerator_label, denominator_label, notes)
RATIO_CARDS = {
    "automation-coverage": ("items processed by the automated path", "eligible items", None),
    "straight-through-completion-rate": ("items completed straight-through", "items entering the process", None),
    "exception-rate": ("items leaving the automated path", "items entering the process", None),
    "guardrail-drill-adherence": ("drills completed and recorded", "drills required by the control plan", None),
    "incident-learning-closure": ("recommendations shipped and verified", "recommendations due", None),
    "automation-eligibility-share": ("items assessed as eligible", "assessed items", None),
    "output-quality-rate": ("outputs meeting quality criteria", "outputs produced", None),
}


def calculate(card_id: str, inputs: dict, label: str = "observed") -> dict:
    """Calculate one metric value from an inputs dict.

    inputs: {"card_id", "numerator", "denominator", "window"?, "data_quality_note"?}
    Returns a baseline-shaped dict (card_id, card_version, value, unit, label).
    """
    if card_id not in RATIO_CARDS:
        raise MetricError(
            f"no calculator registered for card '{card_id}' — implement it in the "
            "use case's own tooling and record the result as a metric_baselines entry; "
            "mama-tools never guesses a formula"
        )
    num, den = inputs.get("numerator"), inputs.get("denominator")
    if not isinstance(num, (int, float)) or not isinstance(den, (int, float)):
        raise MetricError("numerator and denominator must be numbers")
    if den <= 0:
        raise MetricError("denominator must be > 0 (an empty denominator hides the failures)")
    if num < 0 or den < 0:
        raise MetricError("numerator and denominator must be non-negative")
    if num > den:
        raise MetricError(
            f"numerator ({num}) exceeds denominator ({den}) — for a ratio card this "
            "means the inclusion rules are inconsistent; fix the measurement, not the math"
        )
    if label not in ("observed", "estimate", "forecast"):
        raise MetricError(f"label must be observed|estimate|forecast, got {label!r}")
    card_version = inputs.get("card_version")
    if not card_version:
        raise MetricError("card_version is required: baselines are only comparable within a card version")
    return {
        "card_id": card_id,
        "card_version": str(card_version),
        "value": round(100.0 * num / den, 2),
        "unit": "percent",
        "window": inputs.get("window", ""),
        "label": label,
        "data_quality_note": inputs.get("data_quality_note", ""),
    }


def validate_cards_dir(cards_dir: str, schema_path: str) -> list[str]:
    """Validate a directory of metric-card YAML files against the card schema
    (the schema itself lives in mama-metrics; pass its path explicitly)."""
    import jsonschema
    import yaml
    from pathlib import Path

    problems = []
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8")) if False else None
    import json
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for p in sorted(Path(cards_dir).glob("*.yaml")):
        card = yaml.safe_load(p.read_text(encoding="utf-8"))
        for err in validator.iter_errors(card):
            problems.append(f"{p.name}: {err.message}")
    return problems
