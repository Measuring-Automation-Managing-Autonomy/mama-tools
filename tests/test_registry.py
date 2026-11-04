import json
import pytest
from mama_tools.registry import validate_record, load_registry_dir
from mama_tools.errors import RecordValidationError


def base_record():
    return {
        "schema_version": "1.0.0",
        "id": "usecase-invoice-processing",
        "title": "Invoice processing automation",
        "owner": "ops-lead",
        "risk_tier": "medium",
        "lifecycle": "operate",
    }


def test_valid_minimal_record():
    assert validate_record(base_record()) == []


def test_id_pattern_enforced():
    r = base_record()
    r["id"] = "Invoice_Processing"
    problems = validate_record(r)
    assert any("id:" in p for p in problems)


def test_lifecycle_and_risk_enum():
    r = base_record()
    r["lifecycle"] = "flying"
    r["risk_tier"] = "extreme"
    problems = validate_record(r)
    assert any("lifecycle:" in p for p in problems)
    assert any("risk_tier:" in p for p in problems)


def test_practice_stage_range():
    r = base_record()
    r["practice_profile"] = {"model_version": "0.2.0", "stages": {"D-A": 5}}
    problems = validate_record(r)
    assert any("stage must be an integer 0..4" in p for p in problems)


def test_unknown_practice_dimension():
    r = base_record()
    r["practice_profile"] = {"stages": {"D-Z": 2}}
    problems = validate_record(r)
    assert any("unknown dimension" in p for p in problems)


def test_stage_2_requires_evidence():
    r = base_record()
    r["practice_profile"] = {"stages": {"D-A": 2}}
    problems = validate_record(r)
    assert any("without evidence references" in p for p in problems)
    r["practice_profile"]["evidence"] = [{"dimension": "D-A", "ref": "drill-log-2026Q4"}]
    assert validate_record(r) == []


def test_baseline_label_enum():
    r = base_record()
    r["metric_baselines"] = [{"card_id": "exception-rate", "card_version": "0.1.0", "value": 3.2, "label": "truthy"}]
    problems = validate_record(r)
    assert any("label must be observed|estimate|forecast" in p for p in problems)


def test_decision_requires_rationale():
    r = base_record()
    r["decisions"] = [{"date": "2026-11-05", "move": "expand"}]
    problems = validate_record(r)
    assert any("rationale" in p for p in problems)


def test_registry_dir_raises_on_invalid(tmp_path):
    bad = base_record(); bad["lifecycle"] = "nope"
    (tmp_path / "bad.yaml").write_text(json.dumps(bad))
    (tmp_path / "good.yaml").write_text(json.dumps(base_record()))
    with pytest.raises(RecordValidationError):
        load_registry_dir(tmp_path)


def test_registry_dir_loads_valid(tmp_path):
    (tmp_path / "good.yaml").write_text(json.dumps(base_record()))
    recs = load_registry_dir(tmp_path)
    assert [r["id"] for r in recs] == ["usecase-invoice-processing"]
