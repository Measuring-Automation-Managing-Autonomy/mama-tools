import json
import subprocess
import sys
from mama_tools.cli import main


def run_main(argv):
    return main(argv)


def test_metric_calc_json(capsys, tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"numerator": 2, "denominator": 50, "card_version": "0.1.0"}))
    rc = run_main(["metric", "calc", "exception-rate", str(p)])
    out = capsys.readouterr().out
    assert rc == 0 and json.loads(out)["value"] == 4.0


def test_metric_calc_error_exit_code(capsys, tmp_path):
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"numerator": 1, "denominator": 0, "card_version": "0.1.0"}))
    rc = run_main(["metric", "calc", "exception-rate", str(p)])
    assert rc == 2


def test_metric_cards_lists_registry(capsys):
    rc = run_main(["metric", "cards"])
    out = capsys.readouterr().out
    assert "exception-rate" in out and "guardrail-drill-adherence" in out
