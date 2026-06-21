"""Standalone ingest CLI.

Usage:
    python -m ingest.cli run                 # one-shot full ingest
    python -m ingest.cli run --source ashby  # only Ashby boards
    python -m ingest.cli verify              # ping every slug, report 200/404
"""
from __future__ import annotations

import argparse
import asyncio
import logging

import httpx

from db import init_db
from ingest.companies import COMPANIES
from ingest.runner import run_ingest


def _setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


async def _verify():
    """Quick HEAD/GET ping for every slug to catch typos early."""
    from ingest.adapters import ashby, greenhouse, lever, recruitee, workable

    URLS = {
        "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
        "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
        "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
        "workable": "https://apply.workable.com/api/v1/widget/accounts/{slug}",
        "recruitee": "https://{slug}.recruitee.com/api/offers/",
    }
    ok, bad = 0, 0
    async with httpx.AsyncClient(timeout=15.0) as client:
        for c in COMPANIES:
            url = URLS[c["source"]].format(slug=c["slug"])
            try:
                r = await client.get(url, follow_redirects=True)
                status = r.status_code
            except httpx.HTTPError as e:
                status = f"err:{e!s}"
            mark = "✓" if str(status) == "200" else "✗"
            if mark == "✓":
                ok += 1
            else:
                bad += 1
            print(f"  {mark} [{c['source']:10s}/{c['slug']:20s}] {c['name']:20s} → {status}")
    print(f"\nResults: {ok} OK, {bad} failed")


def main():
    _setup_logging()
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    init_db()  # establish motor client before runner uses get_db()

    p = argparse.ArgumentParser("jobcity-ingest")
    sub = p.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="One-shot ingest run.")
    run_p.add_argument("--source", action="append", help="Limit to one ATS source (can repeat).")
    sub.add_parser("verify", help="Ping every slug, report which are 404.")
    args = p.parse_args()

    if args.cmd == "run":
        summary = asyncio.run(run_ingest(only_sources=args.source))
        print(summary)
    elif args.cmd == "verify":
        asyncio.run(_verify())


if __name__ == "__main__":
    main()
