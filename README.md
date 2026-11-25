# dora-metrics-dashboard

Compute and visualise the four **DORA** delivery metrics: deployment frequency, lead time for changes, change failure rate and time to restore, from a simple JSON file or GitHub releases.

## Quick start
```bash
pip install -r requirements.txt
python -m dora.cli sample_data/deployments.json --days 90
streamlit run app.py
```

## Input format
```json
{"id": "d1", "deployed_at": "2026-03-02T10:00:00Z", "first_commit_at": "2026-02-27T15:00:00Z",
 "failed": false, "restored_at": null}
```

## GitHub releases mode
`python -m dora.cli --repo owner/name` treats published releases as deployments and measures lead time from the first commit since the previous release. **This is an approximation.** GitHub cannot tell which releases failed, so releases named hotfix/rollback/revert are flagged and restore times stay empty. For accurate numbers, export deploy and incident data from your CI/CD and incident tooling into the JSON shape above.

## Using the numbers well
- Medians, not averages. Trends, not labels. Never compare teams against each other.
- The performance band is deliberately coarse; use it for conversation, not ranking.

## Tests
```bash
pytest -q
```
