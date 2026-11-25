"""The four DORA metrics from a plain list of deployment records.

Deployment record (ISO-8601 UTC timestamps):
{
  "id": "d1",
  "deployed_at": "2026-03-02T10:00:00Z",
  "first_commit_at": "2026-02-27T15:00:00Z",   # earliest commit shipped in this deploy
  "failed": false,                              # caused a degradation / rollback / hotfix
  "restored_at": null                           # when service was restored, if failed
}
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import median


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _hours(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 3600


def deployment_frequency(deploys: list[dict], period_days: int) -> float:
    """Deployments per day over the period."""
    return round(len(deploys) / period_days, 3) if period_days > 0 else 0.0


def lead_time_hours(deploys: list[dict]) -> float | None:
    """Median hours from first commit to production."""
    vals = [_hours(_dt(d["first_commit_at"]), _dt(d["deployed_at"]))
            for d in deploys if d.get("first_commit_at")]
    vals = [v for v in vals if v >= 0]
    return round(median(vals), 2) if vals else None


def change_failure_rate(deploys: list[dict]) -> float | None:
    return round(sum(bool(d.get("failed")) for d in deploys) / len(deploys), 3) if deploys else None


def mttr_hours(deploys: list[dict]) -> float | None:
    """Median hours to restore service across failed deployments that have a restore time."""
    vals = [_hours(_dt(d["deployed_at"]), _dt(d["restored_at"]))
            for d in deploys if d.get("failed") and d.get("restored_at")]
    return round(median(vals), 2) if vals else None


def classify(freq_per_day: float, lead_h: float | None, cfr: float | None, mttr_h: float | None) -> str:
    """Rough performance band, simplified from the published DORA research.
    Thresholds are intentionally coarse: use trends over time, not the label."""
    if lead_h is None or cfr is None:
        return "insufficient data"
    score = 0
    score += 3 if freq_per_day >= 1 else 2 if freq_per_day >= 1 / 7 else 1 if freq_per_day >= 1 / 30 else 0
    score += 3 if lead_h <= 24 else 2 if lead_h <= 24 * 7 else 1 if lead_h <= 24 * 30 else 0
    score += 3 if cfr <= 0.15 else 2 if cfr <= 0.30 else 1 if cfr <= 0.45 else 0
    if mttr_h is not None:
        score += 3 if mttr_h <= 1 else 2 if mttr_h <= 24 else 1 if mttr_h <= 24 * 7 else 0
        top = 12
    else:
        top = 9
    ratio = score / top
    return "elite" if ratio >= 0.85 else "high" if ratio >= 0.6 else "medium" if ratio >= 0.35 else "low"


def summarize(deploys: list[dict], period_days: int) -> dict:
    f = deployment_frequency(deploys, period_days)
    lt, cfr, mt = lead_time_hours(deploys), change_failure_rate(deploys), mttr_hours(deploys)
    return {
        "period_days": period_days, "deployments": len(deploys),
        "deployment_frequency_per_day": f, "lead_time_hours_median": lt,
        "change_failure_rate": cfr, "mttr_hours_median": mt,
        "band": classify(f, lt, cfr, mt),
    }


def weekly_trend(deploys: list[dict]) -> list[dict]:
    """Per ISO-week deployments and median lead time, for charts."""
    weeks: dict[str, list[dict]] = {}
    for d in deploys:
        y, w, _ = _dt(d["deployed_at"]).isocalendar()
        weeks.setdefault(f"{y}-W{w:02d}", []).append(d)
    return [{"week": k, "deployments": len(v), "lead_time_hours_median": lead_time_hours(v),
             "change_failure_rate": change_failure_rate(v)} for k, v in sorted(weeks.items())]
