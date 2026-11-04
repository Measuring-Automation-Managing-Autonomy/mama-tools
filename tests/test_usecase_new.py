import json
import pytest
from mama_tools.registry import scaffold, validate_record
from mama_tools.errors import RecordValidationError


def test_scaffold_validates_clean():
    rec = scaffold("usecase-demo", "Demo use case", "ops-lead")
    assert validate_record(rec) == []
    assert rec["lifecycle"] == "intake" and rec["risk_tier"] == "medium"


def test_scaffold_rejects_bad_id():
    with pytest.raises(RecordValidationError, match="id:"):
        scaffold("Demo Use Case", "Demo", "ops-lead")


def test_scaffold_rejects_bad_risk_tier():
    with pytest.raises(RecordValidationError, match="risk_tier"):
        scaffold("usecase-demo", "Demo", "ops-lead", risk_tier="extreme")
