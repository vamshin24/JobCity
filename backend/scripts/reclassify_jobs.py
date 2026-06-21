"""Recompute classifier-derived fields on every existing job row.

Use this after editing :mod:`ingest.classify` to update existing data without
running a full ATS ingest. Idempotent.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from db import init_db
from ingest.classify import classify


async def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    db = init_db()
    cursor = db.jobs.find({}, {"_id": 1, "title": 1})
    n = 0
    by_cat: dict[str, int] = {}
    async for doc in cursor:
        cat = classify(doc.get("title") or "")
        await db.jobs.update_one({"_id": doc["_id"]}, {"$set": {"category": cat}})
        by_cat[cat] = by_cat.get(cat, 0) + 1
        n += 1
    print(f"Reclassified {n} jobs:")
    for k, v in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {k:12s} {v}")


if __name__ == "__main__":
    asyncio.run(main())
