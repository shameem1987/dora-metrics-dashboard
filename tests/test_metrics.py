import json

from dora.metrics import (change_failure_rate, classify, deployment_frequency,
                          lead_time_hours, mttr_hours, summarize, weekly_trend)

D = json.load(open("sample_data/deployments.json"))


def test_frequency():
    assert deployment_frequency(D, 30) == 0.2
    assert deployment_frequency(D, 0) == 0.0


def test_lead_time_median():
    # hours: 67, 29, 73, 32, 71, 23.5 -> sorted 23.5, 29, 32, 67, 71, 73 -> median (32+67)/2
    assert lead_time_hours(D) == 49.5


def test_cfr_and_mttr():
    assert change_failure_rate(D) == 0.333
    assert mttr_hours(D) == 2.75           # median of 1.5h and 4h


def test_empty_inputs_are_none_not_crash():
    assert lead_time_hours([]) is None and change_failure_rate([]) is None and mttr_hours([]) is None
    assert summarize([], 30)["band"] == "insufficient data"


def test_negative_lead_time_rows_are_ignored():
    bad = [{"deployed_at": "2026-01-01T00:00:00Z", "first_commit_at": "2026-01-02T00:00:00Z"}]
    assert lead_time_hours(bad) is None


def test_classify_extremes():
    assert classify(2, 2, 0.05, 0.5) == "elite"
    assert classify(0.01, 24 * 90, 0.6, 24 * 30) == "low"


def test_weekly_trend_groups_by_iso_week():
    t = weekly_trend(D)
    assert sum(w["deployments"] for w in t) == 6
    assert t[0]["week"].startswith("2026-W")
