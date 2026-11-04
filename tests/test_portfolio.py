import json
from mama_tools.portfolio import build_view
from mama_tools.registry import load_registry_dir, validate_record


def record_with_practice_and_metrics():
    r = {
        "schema_version": "1.0.0",
        "id": "usecase-refunds-agent",
        "title": "Refund decision agent",
        "owner": "support-director",
        "risk_tier": "high",
        "lifecycle": "review",
        "domains": [{"unit": "support-refund-agent", "domain": "customer-refunds", "contract_id": "refund-agent-v2"}],
        "metric_baselines": [
            {"card_id": "exception-rate", "card_version": "0.1.0", "value": 4.1, "unit": "percent", "label": "observed", "window": "2026-10"}
        ],
        "practice_profile": {
            "model_version": "0.2.0",
            "stages": {"D-A": 3, "D-B": 4, "D-C": 2, "D-D": 3, "D-E": 2},
            "evidence": [{"dimension": "D-A", "ref": "drill-log"}],
        },
    }
    assert validate_record(r) == []
    return r


def test_view_shows_columns_separately(tmp_path):
    (tmp_path / "uc.yaml").write_text(json.dumps(record_with_practice_and_metrics()))
    view = build_view(tmp_path)
    assert "exception-rate" in view
    assert "practice profile" in view and "D-A:3" in view
    assert "never combined" in view


def test_view_without_autonomy_shows_how(tmp_path):
    (tmp_path / "uc.yaml").write_text(json.dumps(record_with_practice_and_metrics()))
    view = build_view(tmp_path)
    assert "mama-tools[autonomy]" in view


def test_view_with_ledger(tmp_path):
    (tmp_path / "uc.yaml").write_text(json.dumps(record_with_practice_and_metrics()))
    ledger = {"schema": 2, "contracts": [{
        "id": "refund-agent-v2", "unit": "support-refund-agent", "domain": "customer-refunds",
        "level": 3, "status": "active",
        "scope": "s", "guardrails": ["g"], "telemetry": ["t"], "revocation_triggers": ["r"],
        "grantor": "support-director", "horizon": "2026-12-31", "last_review": "2026-10-01",
    }]}
    view = build_view(tmp_path, ledger=ledger)
    assert "L3 (active) [mama, as issued]" in view


def test_view_flags_unmatched_domain(tmp_path):
    r = record_with_practice_and_metrics()
    r["domains"][0]["contract_id"] = "unknown-contract"
    (tmp_path / "uc.yaml").write_text(json.dumps(r))
    view = build_view(tmp_path, ledger={"schema": 2, "contracts": []})
    assert "no matching ledger contract" in view
