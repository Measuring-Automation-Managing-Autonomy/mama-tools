"""Use-case registry: schema-validated records with stable IDs.

A use-case record is the MAMA-side join point: it links a unit × domain (the
mama autonomy side) to automation baselines, practice profile, value
hypothesis, evidence, and decisions — each labeled and versioned. Records are
local YAML/JSON files; nothing leaves the machine.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import jsonschema

from .errors import RecordValidationError

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "schemas" / "usecase-record.schema.json"

_ID_RE = re.compile(r"^usecase-[a-z0-9]+(-[a-z0-9]+)*$")
LIFECYCLE = ("intake", "baseline", "map-assess", "control-review", "operate", "review", "retired")
RISK_TIERS = ("low", "medium", "high")
PRACTICE_DIMENSIONS = ("D-A", "D-B", "D-C", "D-D", "D-E")
MOVES = ("continue", "adjust", "expand", "constrain", "retire")


def load_schema(path: Path | None = None) -> dict:
    with open(path or SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _coerce_dates(node):
    """YAML auto-parses unquoted dates into datetime.date objects; the schema
    wants ISO strings. Coerce recursively so users can write natural YAML."""
    import datetime as dt
    if isinstance(node, dt.date) and not isinstance(node, dt.datetime):
        return node.isoformat()
    if isinstance(node, dict):
        return {k: _coerce_dates(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_coerce_dates(v) for v in node]
    return node


def load_record(path: str | Path) -> dict:
    p = Path(path)
    if p.suffix in (".yaml", ".yml"):
        import yaml
        with open(p, encoding="utf-8") as fh:
            return _coerce_dates(yaml.safe_load(fh))
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def validate_record(record: dict, schema_path: str | Path | None = None) -> list[str]:
    """Validate against the schema, then cross-checks the schema cannot express.
    Returns a list of human-readable problems; empty list means valid."""
    problems: list[str] = []
    schema = load_schema(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(x) for x in err.absolute_path) or "(root)"
        problems.append(f"schema: {loc}: {err.message}")

    rid = record.get("id", "")
    if rid and not _ID_RE.match(rid):
        problems.append(f"id: '{rid}' must match usecase-<slug> (lowercase, hyphenated)")
    if record.get("lifecycle") not in LIFECYCLE:
        problems.append(f"lifecycle: '{record.get('lifecycle')}' not in {LIFECYCLE}")
    if record.get("risk_tier") not in RISK_TIERS:
        problems.append(f"risk_tier: '{record.get('risk_tier')}' not in {RISK_TIERS}")

    pp = record.get("practice_profile") or {}
    for dim, stage in (pp.get("stages") or {}).items():
        if dim not in PRACTICE_DIMENSIONS:
            problems.append(f"practice_profile.stages: unknown dimension '{dim}'")
        elif not isinstance(stage, int) or not 0 <= stage <= 4:
            problems.append(f"practice_profile.stages.{dim}: stage must be an integer 0..4")
    # Evidence gate: stage >= 2 requires at least one evidence reference on the profile.
    if pp.get("stages") and any(isinstance(v, int) and v >= 2 for v in pp["stages"].values()):
        if not pp.get("evidence"):
            problems.append(
                "practice_profile: stages >= 2 claimed without evidence references "
                "(maturity-model.md: unevidenced claims record as the stage below)"
            )

    for m in record.get("metric_baselines") or []:
        label = m.get("label")
        if label not in ("observed", "estimate", "forecast"):
            problems.append(f"metric_baselines[{m.get('card_id')}]: label must be observed|estimate|forecast")

    for d in record.get("decisions") or []:
        if d.get("move") not in MOVES:
            problems.append(f"decisions: move '{d.get('move')}' not in {MOVES}")
        if not d.get("rationale"):
            problems.append("decisions: every decision carries a rationale (audit trail)")
    return problems


def load_registry_dir(directory: str | Path) -> list[dict]:
    """Load all use-case records from a directory; raises on the first invalid one."""
    records = []
    for p in sorted(Path(directory).glob("*.y*ml")) + sorted(Path(directory).glob("*.json")):
        rec = load_record(p)
        problems = validate_record(rec)
        if problems:
            raise RecordValidationError(f"{p.name}: " + "; ".join(problems[:5]))
        records.append(rec)
    return records
