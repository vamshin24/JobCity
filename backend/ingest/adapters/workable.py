"""Workable job-board adapter.

Endpoint:  GET https://apply.workable.com/api/v1/widget/accounts/{slug}
Auth:      none
Response:  {"name":..., "jobs":[{shortcode, title, country, city, state, telecommuting,
                                 employment_type, full_description, application_url, ...}]}
Notes:
  - The "jobs" array is paginated by `?limit=50&offset=N` on some boards; the
    widget endpoint returns up to ~50 items by default which is plenty here.
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

_BASE = "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true"


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
        sid = str(j.get("shortcode") or j.get("id") or "")
        if not sid:
            continue
        title = j.get("title") or ""
        # Workable splits city/state out, but also publishes telecommuting flag
        city_raw = j.get("city") or ""
        state_raw = j.get("state") or j.get("region") or ""
        country = j.get("country") or ""
        location_str = ", ".join(p for p in (city_raw, state_raw, country) if p)
        body = html_to_text(j.get("description") or j.get("full_description") or "")
        if j.get("requirements"):
            body += " " + html_to_text(j.get("requirements"))
        if j.get("benefits"):
            body += " " + html_to_text(j.get("benefits"))
        body = body[:4000]
        is_remote = bool(j.get("telecommuting")) or detect_remote(location_str, title)
        city, state, coords = parse_location(location_str)
        if is_remote:
            city, state, coords = remote_city_for(job_id_for("workable", sid))
        if not city:
            continue
        lo, hi = extract_salary_range(body)
        out.append(
            NormalizedJob(
                job_id=job_id_for("workable", sid),
                source="workable",
                source_id=sid,
                source_url=j.get("url") or j.get("application_url") or "",
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
                posted_at=parse_posted_at(j.get("published_on") or j.get("created_at")),
                is_active=True,
                ingested_at=now,
            )
        )
    return out
