import pytest
from mama_tools.metrics import calculate
from mama_tools.errors import MetricError


def test_basic_ratio():
    r = calculate("exception-rate", {"numerator": 3, "denominator": 200, "card_version": "0.1.0"})
    assert r["value"] == 1.5 and r["unit"] == "percent" and r["label"] == "observed"


def test_unknown_card_refused():
    with pytest.raises(MetricError, match="no calculator registered"):
        calculate("made-up-card", {"numerator": 1, "denominator": 10, "card_version": "0.1.0"})


def test_zero_denominator_refused():
    with pytest.raises(MetricError, match="empty denominator"):
        calculate("automation-coverage", {"numerator": 0, "denominator": 0, "card_version": "0.1.0"})


def test_numerator_gt_denominator_refused():
    with pytest.raises(MetricError, match="inclusion rules are inconsistent"):
        calculate("straight-through-completion-rate", {"numerator": 12, "denominator": 10, "card_version": "0.1.0"})


def test_card_version_required():
    with pytest.raises(MetricError, match="card_version is required"):
        calculate("exception-rate", {"numerator": 1, "denominator": 10})


def test_label_enum():
    with pytest.raises(MetricError, match="label must be"):
        calculate("exception-rate", {"numerator": 1, "denominator": 10, "card_version": "0.1.0"}, label="vibes")


def test_negative_refused():
    with pytest.raises(MetricError, match="non-negative"):
        calculate("exception-rate", {"numerator": -1, "denominator": 10, "card_version": "0.1.0"})


def test_estimate_label_roundtrip():
    r = calculate("guardrail-drill-adherence", {"numerator": 7, "denominator": 8, "card_version": "0.1.0"}, label="estimate")
    assert r["label"] == "estimate" and r["value"] == 87.5
