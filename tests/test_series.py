import json
import pytest
from mama_tools.series import import_rows, append_series, load_series
from mama_tools.errors import RecordValidationError

CSV = """usecase_id,card_id,card_version,window,value,label,source_note
usecase-a,automation-coverage,0.1.0,2026-10,72.5,observed,workflow logs
usecase-a,exception-rate,0.1.0,2026-10,4.1,observed,tickets v3
"""


def test_csv_import_ok(tmp_path):
    f = tmp_path / "s.csv"; f.write_text(CSV)
    rows = import_rows(f, registry_ids={"usecase-a"})
    assert len(rows) == 2 and rows[0]["value"] == 72.5


def test_unlabeled_row_rejected(tmp_path):
    f = tmp_path / "s.csv"; f.write_text("usecase_id,card_id,card_version,window,value,label\nusecase-a,automation-coverage,0.1.0,2026-10,72.5,\n")
    with pytest.raises(RecordValidationError, match="label"):
        import_rows(f)


def test_orphan_usecase_rejected(tmp_path):
    f = tmp_path / "s.csv"; f.write_text(CSV)
    with pytest.raises(RecordValidationError, match="no orphans|not in the registry"):
        import_rows(f, registry_ids={"usecase-other"})


def test_bad_card_version_rejected(tmp_path):
    f = tmp_path / "s.csv"; f.write_text("usecase_id,card_id,card_version,window,value,label\nusecase-a,automation-coverage,1.0,2026-10,72.5,observed\n")
    with pytest.raises(RecordValidationError, match="semver"):
        import_rows(f)


def test_append_and_load_roundtrip(tmp_path):
    f = tmp_path / "s.json"
    rows = [{"usecase_id": "usecase-a", "card_id": "automation-coverage", "card_version": "0.1.0",
             "window": "2026-10", "value": 50, "label": "observed"},
            {"usecase_id": "usecase-a", "card_id": "automation-coverage", "card_version": "0.1.0",
             "window": "2026-11", "value": 60, "label": "observed"}]
    f.write_text(json.dumps({"rows": rows}))
    imported = import_rows(f, registry_ids=None)
    assert append_series(tmp_path / "series", imported) == 2
    got = load_series(tmp_path / "series", "usecase-a", "automation-coverage")
    assert [g["window"] for g in got] == ["2026-10", "2026-11"]
