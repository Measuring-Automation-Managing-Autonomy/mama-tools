"""The series interface: import card-versioned, labeled metric observations.

This is the seam between an organization's own measurement systems and MAMA
computation (indices-and-tracking.md section 4). Rows are append-only:
importing never edits prior series data. The autonomy axis has NO series
seam — delegated-authority numbers flow only through the version-gated
mama-integrations import.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .errors import RecordValidationError

_ROW_RE = re.compile(r"^usecase-[a-z0-9]+(-[a-z0-9]+)*$")
LABELS = ("observed", "estimate", "forecast")


def _check_row(row: dict, registry_ids: set[str] | None) -> dict:
    for field in ("usecase_id", "card_id", "card_version", "window", "value", "label"):
        if row.get(field) in (None, ""):
            raise RecordValidationError(f"row missing required field '{field}': {row}")
    if not _ROW_RE.match(str(row["usecase_id"])):
        raise RecordValidationError(f"usecase_id '{row['usecase_id']}' must match usecase-<slug>")
    if registry_ids is not None and row["usecase_id"] not in registry_ids:
        raise RecordValidationError(
            f"usecase_id '{row['usecase_id']}' is not in the registry — linkage must be explicit (no orphans)"
        )
    if not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", str(row["card_version"])):
        raise RecordValidationError(f"card_version '{row['card_version']}' must be semver")
    if row["label"] not in LABELS:
        raise RecordValidationError(f"label must be one of {LABELS}, got {row['label']!r}")
    try:
        row["value"] = float(row["value"])
    except (TypeError, ValueError):
        raise RecordValidationError(f"value must be a number, got {row['value']!r}")
    return {k: row.get(k, "") for k in
            ("usecase_id", "card_id", "card_version", "window", "value", "label", "source_note")}


def import_rows(path: str | Path, registry_ids: set[str] | None = None) -> list[dict]:
    """Import observations from a CSV or JSON file; returns validated rows."""
    p = Path(path)
    rows: list[dict] = []
    if p.suffix == ".csv":
        with open(p, encoding="utf-8-sig", newline="") as fh:
            for i, raw in enumerate(csv.DictReader(fh), start=2):
                try:
                    rows.append(_check_row({k: (v or "").strip() for k, v in raw.items()}, registry_ids))
                except RecordValidationError as exc:
                    raise RecordValidationError(f"line {i}: {exc}") from exc
    elif p.suffix == ".json":
        doc = json.loads(p.read_text(encoding="utf-8"))
        rows = doc.get("rows", []) if isinstance(doc, dict) else doc
        rows = [_check_row(dict(r), registry_ids) for r in rows]
    else:
        raise RecordValidationError("series file must be .csv or .json")
    if not rows:
        raise RecordValidationError("series file contains no rows")
    return rows


def append_series(series_dir: str | Path, rows: list[dict]) -> int:
    """Append validated rows to per-use-case series files (JSONL, append-only).
    Returns the number of rows written."""
    sdir = Path(series_dir)
    sdir.mkdir(parents=True, exist_ok=True)
    written = 0
    by_usecase: dict[str, list[dict]] = {}
    for r in rows:
        by_usecase.setdefault(r["usecase_id"], []).append(r)
    for uc, uc_rows in by_usecase.items():
        f = sdir / f"{uc}.series.jsonl"
        with open(f, "a", encoding="utf-8") as fh:
            for r in uc_rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
                written += 1
    return written


def load_series(series_dir: str | Path, usecase_id: str, card_id: str) -> list[dict]:
    """Load one use case's series rows for one card, ordered by window."""
    f = Path(series_dir) / f"{usecase_id}.series.jsonl"
    if not f.exists():
        return []
    rows = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("card_id") == card_id:
            rows.append(r)
    rows.sort(key=lambda r: r["window"])
    return rows
