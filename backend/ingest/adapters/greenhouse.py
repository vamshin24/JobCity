"""Greenhouse job-board adapter.

Endpoint:  GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
Auth:      none
Rate:      generous (we use ≤ a few requests per company per ingest run)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

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

_BASE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


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
        sid = str(j.get("id") or j.get("internal_job_id"))
        if not sid:
            continue
        title = j.get("title") or ""
        location_str = (j.get("location") or {}).get("name") or ""
        if not location_str:
            offices = j.get("offices") or []
            if offices:
                location_str = ", ".join(o.get("name", "") for o in offices)
        body_html = j.get("content") or ""
        body = html_to_text(body_html)
        is_remote = detect_remote(location_str, title)
        city, state, coords = parse_location(location_str)
        if is_remote:
            # Spread remote roles across all known US cities so the map's
            # empty regions get populated instead of piling on HQ.
            city, state, coords = remote_city_for(job_id_for("greenhouse", sid))
        if not city:
            continue
        lo, hi = extract_salary_range(body)
        out.append(
            NormalizedJob(
                job_id=job_id_for("greenhouse", sid),
                source="greenhouse",
                source_id=sid,
                source_url=j.get("absolute_url") or "",
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
                posted_at=parse_posted_at(j.get("updated_at") or j.get("first_published")),
                is_active=True,
                ingested_at=now,
            )
        )
    return out
