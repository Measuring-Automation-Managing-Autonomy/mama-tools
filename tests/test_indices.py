import json
import pytest
from mama_tools.indices import build_tracker_record, autonomy_axis, render_markdown, render_svg
from mama_tools.registry import load_registry_dir
from mama_tools.errors import MamaToolsError

LEDGER = {"schema": 2, "contracts": [
    {"id": "refund-agent-v2", "unit": "support-refund-agent", "domain": "customer-refunds",
     "level": 4, "status": "active", "scope": "s", "guardrails": ["g"], "telemetry": ["t"],
     "revocation_triggers": ["r"], "grantor": "support-director", "horizon": "2026-12-31",
     "last_review": "2026-10-01"},
    {"id": "refund-agent-docs", "unit": "support-refund-agent", "domain": "docs-updates",
     "level": 2, "status": "active", "scope": "s", "guardrails": ["g"], "telemetry": ["t"],
     "revocation_triggers": ["r"], "grantor": "support-director", "horizon": "2026-12-31",
     "last_review": "2026-10-01"},
]}


def record():
    return {
        "schema_version": "1.0.0", "id": "usecase-refunds-agent", "title": "Refund agent",
        "owner": "support-director", "risk_tier": "high", "lifecycle": "review",
        "domains": [{"unit": "support-refund-agent", "domain": "customer-refunds",
                     "contract_id": "refund-agent-v2"},
                    {"unit": "support-refund-agent", "domain": "docs-updates",
                     "contract_id": "refund-agent-docs"}],
        "metric_baselines": [{"card_id": "automation-coverage", "card_version": "0.1.0",
                              "value": 72.5, "unit": "percent", "label": "observed",
                              "window": "2026-10"}],
    }


def test_autonomy_axis_mean_and_floor():
    ax, warnings = autonomy_axis(record()["domains"], LEDGER)
    assert warnings == []
    assert ax["mean_level"] == 3.0 and ax["index"] == 60.0
    assert ax["min_level"] == 2 and ax["domains"] == 2


def test_autonomy_floor_zero_flags_submarine():
    led = {"schema": 2, "contracts": [dict(LEDGER["contracts"][0], level=0)]}
    t = build_tracker_record(record(), None, led)
    assert t["axes"]["autonomy"]["min_level"] == 0
    assert any("SUBMARINE LINE" in n for n in t["notes"])


def test_tracker_record_shape_and_no_imputation():
    t = build_tracker_record(record(), None, None)
    assert t["axes"]["automation"]["value"] == 72.5
    assert t["axes"]["autonomy"] is None and t["axes"]["value"] is None
    assert t["provenance"]["tool"] == "mama-tools"


def test_report_carries_floor_and_caption():
    t = build_tracker_record(record(), None, LEDGER)
    md = render_markdown([t])
    assert "floor" in md and "as issued" in md and "never a composite" in md


def test_svg_parses_and_carries_rule():
    import xml.etree.ElementTree as ET
    t = build_tracker_record(record(), None, LEDGER)
    svg = render_svg([t])
    root = ET.fromstring(svg)
    assert "never a composite" in svg and "ADR-003/005" in svg
    assert len(root.findall("{http://www.w3.org/2000/svg}circle")) == 1
