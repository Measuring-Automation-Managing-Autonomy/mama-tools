"""Portfolio view: side-by-side display, by construction never blended.

Renders per use case: automation/value baselines, the practice profile, and
— when mama-integrations is installed and a ledger path is given — the mama
autonomy profile exactly as issued. No totals, no scores, no joins between
the columns (mama-framework ADR-003).
"""
from __future__ import annotations

from .registry import load_registry_dir


def _autonomy_rows(record: dict, ledger: dict | None):
    """Return (level, contract_id, status) per domain, matching ledger contracts
    by contract_id or unit+domain. Only possible with a loaded ledger dict."""
    contracts = {c.get("id"): c for c in (ledger or {}).get("contracts", [])}
    rows = []
    for d in record.get("domains", []):
        c = contracts.get(d.get("contract_id") or "")
        if c is None:
            c = next(
                (x for x in (ledger or {}).get("contracts", [])
                 if x.get("unit") == d.get("unit") and x.get("domain") == d.get("domain")),
                None,
            )
        if c is None:
            rows.append((d["unit"], d["domain"], "no matching ledger contract", ""))
        else:
            rows.append((d["unit"], d["domain"], f"L{c.get('level')}", c.get("status", "")))
    return rows


def build_view(registry_dir: str, ledger: dict | None = None) -> str:
    records = load_registry_dir(registry_dir)
    lines = []
    lines.append("MAMA portfolio view — measures displayed side by side, never combined")
    lines.append("(ADR-003: no composite; automation metrics, autonomy profiles, and")
    lines.append(" practice profiles are separate instruments read by humans.)")
    lines.append("=" * 72)
    if not records:
        lines.append("(registry empty)")
        return "\n".join(lines)
    for r in records:
        lines.append(f"{r['id']}  {r['title']}")
        lines.append(f"  owner: {r['owner']}   risk tier: {r['risk_tier']}   lifecycle: {r['lifecycle']}")
        mb = r.get("metric_baselines") or []
        if mb:
            lines.append("  automation/value baselines:")
            for m in mb:
                lines.append(
                    f"    - {m['card_id']} v{m['card_version']}: {m['value']} {m.get('unit', '')} "
                    f"[{m['label']}] {m.get('window', '')}"
                )
        else:
            lines.append("  automation/value baselines: (none recorded)")
        pp = (r.get("practice_profile") or {}).get("stages") or {}
        if pp:
            stages = "  ".join(f"{k}:{v}" for k, v in sorted(pp.items()))
            lines.append(f"  practice profile (descriptive, evidence-gated): {stages}")
        else:
            lines.append("  practice profile: (not assessed)")
        if ledger is not None:
            for unit, domain, level, status in _autonomy_rows(r, ledger):
                lines.append(f"  autonomy: {unit} / {domain} -> {level} ({status}) [mama, as issued]")
        else:
            lines.append(
                "  autonomy: unavailable — install mama-tools[autonomy] and pass the ledger "
                "(imported as-issued via mama-integrations; never recomputed here)"
            )
        lines.append("")
    return "\n".join(lines)
