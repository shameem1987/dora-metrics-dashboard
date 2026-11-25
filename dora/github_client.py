"""Build deployment records from GitHub *releases* + their commits.

Approximation, stated plainly: a published release is treated as a production deploy.
If you deploy via the Deployments API or your CI, prefer exporting that data to the
JSON shape in dora/metrics.py instead. Failure/restore data cannot be inferred from
GitHub alone, so label hotfix releases yourself (see HOTFIX_HINTS).
"""
from __future__ import annotations

import json
import os
import urllib.request

API = "https://api.github.com"
HOTFIX_HINTS = ("hotfix", "rollback", "revert")


def _get(url: str, token: str | None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "dora-metrics-dashboard"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.loads(r.read().decode())


def deployments_from_releases(repo: str, token: str | None = None, limit: int = 50) -> list[dict]:
    token = token or os.getenv("GITHUB_TOKEN")
    releases = [r for r in _get(f"{API}/repos/{repo}/releases?per_page={min(limit, 100)}", token)
                if not r.get("draft") and r.get("published_at")]
    releases.sort(key=lambda r: r["published_at"])
    out = []
    for prev, cur in zip([None] + releases[:-1], releases):
        first_commit = None
        if prev:
            cmp = _get(f"{API}/repos/{repo}/compare/{prev['tag_name']}...{cur['tag_name']}", token)
            commits = cmp.get("commits", [])
            if commits:
                first_commit = min(c["commit"]["committer"]["date"] for c in commits)
        text = f"{cur.get('name') or ''} {cur.get('tag_name') or ''}".lower()
        out.append({"id": cur["tag_name"], "deployed_at": cur["published_at"],
                    "first_commit_at": first_commit,
                    "failed": any(h in text for h in HOTFIX_HINTS), "restored_at": None})
    return out
