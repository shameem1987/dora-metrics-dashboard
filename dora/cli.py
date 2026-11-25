"""python -m dora.cli sample_data/deployments.json --days 90
   python -m dora.cli --repo owner/name --days 90"""
from __future__ import annotations

import argparse
import json

from .metrics import summarize


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--repo")
    ap.add_argument("--days", type=int, default=90)
    a = ap.parse_args(argv)
    if a.repo:
        from .github_client import deployments_from_releases
        deploys = deployments_from_releases(a.repo)
    elif a.file:
        deploys = json.load(open(a.file))
    else:
        ap.error("provide a JSON file or --repo")
    s = summarize(deploys, a.days)
    print(json.dumps(s, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
