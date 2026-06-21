"""Common normalized Job shape produced by every ATS adapter.

Adapters return dicts conforming to ``NormalizedJob`` — the runner persists
them as-is into the ``jobs`` collection (plus ingestion bookkeeping).
"""
from __future__ import annotations

import hashlib
from typing import Optional, TypedDict


class NormalizedJob(TypedDict, total=False):
    job_id: str               # deterministic: f"{source}_{source_id}"
    source: str               # greenhouse | lever | ashby | workable | recruitee
    source_id: str            # ATS job id (string)
    source_url: str           # canonical job-page URL
    company_id: str           # f"co_{md5(name)[:10]}"
    company_name: str
    company_color: str
    title: str
    description: str          # plain-text, ≤4000 chars
    city: Optional[str]
    state: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    remote: bool
    level: str                # entry | mid | senior
    category: str             # software | robotics | ml | data | security | infra | hardware | design | product | management | business | other
    skills: list[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    posted_at: str            # ISO-8601 UTC
    is_active: bool           # always True at ingest; set False if not re-seen
    ingested_at: str          # ISO-8601 UTC, refreshed every ingest run


def company_id_for(name: str) -> str:
    return f"co_{hashlib.md5(name.encode(), usedforsecurity=False).hexdigest()[:10]}"


def job_id_for(source: str, source_id: str) -> str:
    return f"{source}_{source_id}"
