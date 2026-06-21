"""Ashby job-board adapter.

Endpoint:  GET https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true
Auth:      none
Response:  {"jobs": [{id, title, location, departmentName, descriptionHtml, publishedAt,
                     applyUrl, jobUrl, compensation: {...}, ...}]}
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

import httpx

from ingest.extract import (
    extract_salary_range,
    extract_skills,
    html_to_text,
    infer_level,
    parse_posted_at,
)
from ingest.classify import classify
from ingest.locations import detect_remote, parse_location
from ingest.normalize import NormalizedJob, company_id_for, job_id_for
from ingest.remote_spread import remote_city_for

_BASE = "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"


def _ashby_comp(comp: dict) -> Tuple[Optional[int], Optional[int]]:
    """Ashby compensation is a structured object with compensationTierSummary etc.
    We try the standard cash-range fields first.
    """
    if not comp or not isinstance(comp, dict):
        return (None, None)
    summary = comp.get("compensationTierSummary") or ""
    if summary:
        lo, hi = extract_salary_range(summary)
        if lo and hi:
            return (lo, hi)
    tiers = comp.get("compensationTiers") or []
    for t in tiers:
        for comp_entry in (t.get("components") or []):
            if comp_entry.get("compensationType") == "Salary":
                lo = comp_entry.get("minValue")
                hi = comp_entry.get("maxValue")
                try:
                    lo = int(lo) if lo is not None else None
                    hi = int(hi) if hi is not None else None
                except (TypeError, ValueError):
                    continue
                if lo and hi:
                    if lo < 1000:  # k → dollars
                        lo *= 1000
                    if hi < 1000:
                        hi *= 1000
                    return (lo, hi)
    return (None, None)


async def fetch(company: dict, client: httpx.AsyncClient) -> List[NormalizedJob]:
    url = _BASE.format(slug=company["slug"])
    r = await client.get(url, timeout=20.0)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobs") or []
    out: List[NormalizedJob] = []

    cid = company_id_for(company["name"])
    now = datetime.now(timezone.utc).isoformat()

    for j in jobs:
        sid = str(j.get("id") or "")
        if not sid:
            continue
        title = j.get("title") or ""
        location_str = j.get("location") or ""
        body = html_to_text(j.get("descriptionHtml") or j.get("description") or "")
        is_remote = bool(j.get("isRemote")) or detect_remote(location_str, title)
        city, state, coords = parse_location(location_str)
        if is_remote:
            city, state, coords = remote_city_for(job_id_for("ashby", sid))
        if not city:
            continue
        lo, hi = _ashby_comp(j.get("compensation") or {})
        if not lo:
            lo, hi = extract_salary_range(body)
        out.append(
            NormalizedJob(
                job_id=job_id_for("ashby", sid),
                source="ashby",
                source_id=sid,
                source_url=j.get("jobUrl") or j.get("applyUrl") or "",
                company_id=cid,
                company_name=company["name"],
                company_color=company.get("color", "#5B8DEF"),
                title=title,
                description=body,
                city=city,
                state=state,
                lat=coords[0] if coords else None,
                lng=coords[1] if coords else None,
                remote=is_remote,
                level=infer_level(title, body),
                category=classify(title),
                skills=extract_skills(f"{title}\n{body}"),
                salary_min=lo,
                salary_max=hi,
                posted_at=parse_posted_at(j.get("publishedAt") or j.get("updatedAt")),
                is_active=True,
                ingested_at=now,
            )
        )
    return out
