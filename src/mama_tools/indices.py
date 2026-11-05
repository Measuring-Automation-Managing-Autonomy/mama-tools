"""Per-axis display indices (v1) and the multi-dimensional tracker.

Specified by mama-framework/indices-and-tracking.md and authorized by
ADR-005. The three axes are SEPARATE instruments: no function in this module
combines them, and the rendered artifacts carry the no-composite rule.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import __version__
from .errors import MamaToolsError
from .registry import load_registry_dir
from .series import load_series

TRACKER_VERSION = "1.0.0"


def automation_axis(record: dict, series_dir: str | Path | None) -> dict | None:
    """Automation Index = the automation-coverage card value, as observed.
    Prefers the latest series row; falls back to the record's baseline."""
    uc = record["id"]
    if series_dir:
        rows = [r for r in load_series(series_dir, uc, "automation-coverage") if r["label"] == "observed"]
        if rows:
            last = rows[-1]
            return {"value": last["value"], "card_id": "automation-coverage",
                    "card_version": last["card_version"], "window": last["window"],
                    "label": last["label"]}
    for m in record.get("metric_baselines", []):
        if m["card_id"] == "automation-coverage" and m.get("label") == "observed":
            return {"value": m["value"], "card_id": m["card_id"],
                    "card_version": m["card_version"], "window": m.get("window", ""),
                    "label": m["label"]}
    return None


def value_axis(record: dict, series_dir: str | Path | None) -> dict | None:
    """Value Realization = the realized-vs-forecast-benefit card value.
    May be negative; displayed unclamped. Attribution travels when present."""
    uc = record["id"]
    if series_dir:
        rows = [r for r in load_series(series_dir, uc, "realized-vs-forecast-benefit")]
        if rows:
            last = rows[-1]
            return {"value": last["value"], "card_id": "realized-vs-forecast-benefit",
                    "card_version": last["card_version"], "window": last["window"],
                    "label": last["label"], "attribution": last.get("source_note", "")}
    return None


def autonomy_axis(linked_domains: list[dict], ledger) -> tuple[dict | None, list[str]]:
    """Autonomy Index from ledger granted levels, AS ISSUED.
    Never recomputes weakest-link or dimension scores. The floor (min level)
    is mandatory: a mean can hide a domain at the Submarine Line.
    Accepts a mama-integrations LedgerImportResult (the controlled import)
    or a plain {'schema': int, 'contracts': [...]} dict. Importer warnings
    are returned for the report — fail loud, not silent."""
    if hasattr(ledger, "contracts"):  # mama-integrations LedgerImportResult
        contracts_list = list(ledger.contracts)
        schema_version = ledger.schema_version
        import_warnings = list(ledger.warnings)
    else:
        contracts_list = list(ledger.get("contracts", []))
        schema_version = ledger.get("schema")
        import_warnings = []
    contracts = {c.get("id"): c for c in contracts_list}
    levels = []
    ids = []
    for d in linked_domains:
        c = contracts.get(d.get("contract_id") or "")
        if c is None:
            c = next((x for x in contracts_list
                      if x.get("unit") == d.get("unit") and x.get("domain") == d.get("domain")), None)
        if c is not None and isinstance(c.get("level"), int):
            levels.append(c["level"])
            ids.append(c["id"])
    if not levels:
        return None, import_warnings
    mean_level = sum(levels) / len(levels)
    return {
        "index": round(mean_level * 20, 2),
        "mean_level": round(mean_level, 3),
        "min_level": min(levels),
        "domains": len(levels),
        "ruleset_version": _upstream_ruleset(ledger),
        "ledger_schema": schema_version,
        "contract_ids": ids,
    }, import_warnings


def _upstream_ruleset(ledger) -> str:
    """The ruleset version the ledger was issued under. Ledgers do not carry
    it; the tracker consumer supplies it via the registry/integration layer.
    Recorded as the adapter's supported version here (fail-closed upstream)."""
    try:
        from mama_integrations.versions import SUPPORTED_RULESET_VERSION  # type: ignore
        return SUPPORTED_RULESET_VERSION
    except ImportError:
        return "2.0.0"


def build_tracker_record(record: dict, series_dir: str | Path | None,
                         ledger: dict | None) -> dict:
    warnings: list[str] = []
    axes = {
        "automation": automation_axis(record, series_dir),
        "value": value_axis(record, series_dir),
    }
    axes["autonomy"] = None
    if ledger is not None:
        ax, import_warnings = autonomy_axis(record.get("domains", []), ledger)
        axes["autonomy"] = ax
        warnings += import_warnings
    floor = (axes["autonomy"] or {}).get("min_level")
    notes = list(warnings)
    if floor == 0:
        notes.append("SUBMARINE LINE: at least one linked domain holds no autonomy at all, "
                     "regardless of the index value.")
    pp = (record.get("practice_profile") or {}).get("stages") or {}
    return {
        "tracker_version": TRACKER_VERSION,
        "usecase_id": record["id"],
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "axes": axes,
        "practice_profile": {"stages": pp} if pp else None,
        "provenance": {"tool": "mama-tools", "tool_version": __version__},
        "notes": notes,
    }


def render_markdown(trackers: list[dict]) -> str:
    out = ["# MAMA tracker report",
           "",
           "Display construct — separate instruments, never a composite (mama-framework ADR-003/ADR-005).",
           ""]
    for t in trackers:
        a, au, v = t["axes"]["automation"], t["axes"]["autonomy"], t["axes"]["value"]
        out.append(f"## {t['usecase_id']} — generated {t['generated_at']}")
        out.append(f"- Automation Index: " + (f"**{a['value']}** (card {a['card_id']} v{a['card_version']}, window {a['window']}, {a['label']})" if a else "absent"))
        if au:
            out.append(f"- Autonomy Index: **{au['index']}** (mean level {au['mean_level']} across {au['domains']} domain(s); floor **L{au['min_level']}**; ruleset {au['ruleset_version']}, ledger schema {au['ledger_schema']}) — as issued")
            if au["mean_level"] - au["min_level"] >= 2:
                out.append(f"  - note: the floor is ≥2 levels below the mean — the mean hides a low-grant domain")
        else:
            out.append("- Autonomy Index: absent (no linked ledger contracts measured)")
        out.append("- Value Realization: " + (f"**{v['value']}%** vs. forecast ({v['card_id']} v{v['card_version']}, {v['label']}" + (f", attribution: {v['attribution']}" if v.get("attribution") else "") + ")" if v else "absent (no forecast/realization measured)"))
        for n in t.get("notes", []):
            out.append(f"- ⚠️ {n}")
        pp = (t.get("practice_profile") or {}).get("stages") or {}
        if pp:
            out.append(f"- Practice profile (descriptive): " + ", ".join(f"{k}:{pp[k]}" for k in sorted(pp)))
        out.append("")
    return "\n".join(out)


def render_svg(trackers: list[dict]) -> str:
    """X = automation index, Y = autonomy index, bubble area = |value realization|.
    Floor markers for min_level. The no-composite caption is burned in."""
    def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    W, H, M = 640, 640, 60
    def X(v): return M + (W - 2 * M) * (v / 100.0)
    def Y(v): return H - M - (H - 2 * M) * (v / 100.0)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="MAMA tracker: automation index by autonomy index, bubble size value realization. Display construct - separate instruments, never a composite (ADR-003/ADR-005).">',
             f'<text x="{M}" y="24" font-size="14" fill="#1f4e79">MAMA tracker — separate instruments, never a composite (ADR-003/005)</text>',
             f'<line x1="{M}" y1="{H-M}" x2="{W-M}" y2="{H-M}" stroke="#333"/><line x1="{M}" y1="{H-M}" x2="{M}" y2="{M}" stroke="#333"/>',
             f'<text x="{W/2}" y="{H-20}" text-anchor="middle" font-size="12">Automation Index (automation-coverage, 0–100)</text>',
             f'<text x="20" y="{H/2}" text-anchor="middle" font-size="12" transform="rotate(-90 20 {H/2})">Autonomy Index (mean granted level ×20; floor shown)</text>']
    for t in trackers:
        a, au, v = t["axes"]["automation"], t["axes"]["autonomy"], t["axes"]["value"]
        if not (a and au):
            continue
        cx, cy = X(a["value"]), Y(au["index"])
        r = 6 + min(abs(v["value"]) if v else 0, 100) * 0.25
        fill = "none" if (v and v["value"] < 0) else "#1f4e79"
        stroke = "#b53d00" if (v and v["value"] < 0) else "#1f4e79"
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"><title>{esc(t["usecase_id"])}: automation {a["value"]}, autonomy {au["index"]} (floor L{au["min_level"]}), value {v["value"] if v else "absent"}</title></circle>')
        parts.append(f'<text x="{cx:.1f}" y="{cy - r - 4:.1f}" text-anchor="middle" font-size="10">{esc(t["usecase_id"].replace("usecase-", ""))}</text>')
        fl = au["min_level"] * 20
        parts.append(f'<line x1="{cx - 8:.1f}" y1="{Y(fl):.1f}" x2="{cx + 8:.1f}" y2="{Y(fl):.1f}" stroke="#b53d00" stroke-width="1"><title>{esc(t["usecase_id"])} autonomy floor: L{au["min_level"]}</title></line>')
    parts.append("</svg>")
    return "\n".join(parts)


def write_outputs(out_dir: str | Path, trackers: list[dict]) -> dict:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    paths = {}
    (out / "tracker.jsonl").open("a", encoding="utf-8").write(
        "".join(json.dumps(t, sort_keys=True) + "\n" for t in trackers))
    paths["tracker_jsonl"] = str(out / "tracker.jsonl")
    (out / "tracker-report.md").write_text(render_markdown(trackers), encoding="utf-8")
    paths["report_md"] = str(out / "tracker-report.md")
    (out / "tracker-plot.svg").write_text(render_svg(trackers), encoding="utf-8")
    paths["plot_svg"] = str(out / "tracker-plot.svg")
    return paths
