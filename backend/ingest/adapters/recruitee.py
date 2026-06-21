"""Recruitee job-board adapter.

Endpoint:  GET https://{slug}.recruitee.com/api/offers/
Auth:      none
Response:  {"offers": [{id, slug, title, city, country, location, description, requirements,
                       department, published_at, careers_url, ...}]}
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

_BASE = "https://{slug}.recruitee.com/api/offers/"


async def fetch(company: dict, client: httpx.AsyncClient) -> List[NormalizedJob]:
    url = _BASE.format(slug=company["slug"])
    r = await client.get(url, timeout=20.0)
    r.raise_for_status()
    data = r.json()
    offers = data.get("offers") or []
    out: List[NormalizedJob] = []

    cid = company_id_for(company["name"])
    now = datetime.now(timezone.utc).isoformat()

    for o in offers:
        sid = str(o.get("id") or o.get("slug") or "")
        if not sid:
            continue
        title = o.get("title") or ""
        location_str = o.get("location") or ", ".join(
            p for p in (o.get("city"), o.get("country")) if p
        )
        body = html_to_text(
            (o.get("description") or "") + " " + (o.get("requirements") or "")
        )[:4000]
        is_remote = bool(o.get("remote")) or detect_remote(location_str, title)
        city, state, coords = parse_location(location_str)
        if is_remote:
            city, state, coords = remote_city_for(job_id_for("recruitee", sid))
        if not city:
            continue
        lo, hi = extract_salary_range(body)
        out.append(
            NormalizedJob(
                job_id=job_id_for("recruitee", sid),
                source="recruitee",
                source_id=sid,
                source_url=o.get("careers_url") or o.get("careers_apply_url") or "",
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
                posted_at=parse_posted_at(o.get("published_at") or o.get("created_at")),
                is_active=True,
                ingested_at=now,
            )
        )
    return out
