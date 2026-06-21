"""Lever job-board adapter.

Endpoint:  GET https://api.lever.co/v0/postings/{slug}?mode=json
Auth:      none
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

_BASE = "https://api.lever.co/v0/postings/{slug}?mode=json"


async def fetch(company: dict, client: httpx.AsyncClient) -> List[NormalizedJob]:
    url = _BASE.format(slug=company["slug"])
    r = await client.get(url, timeout=20.0)
    r.raise_for_status()
    postings = r.json() or []
    out: List[NormalizedJob] = []

    cid = company_id_for(company["name"])
    now = datetime.now(timezone.utc).isoformat()

    for p in postings:
        sid = str(p.get("id") or "")
        if not sid:
            continue
        title = p.get("text") or ""
        categories = p.get("categories") or {}
        location_str = categories.get("location") or ""
        if not location_str:
            location_str = categories.get("allLocations") and ", ".join(categories["allLocations"]) or ""
        # Lever description is in `descriptionPlain` or `description` (HTML)
        body = p.get("descriptionPlain") or html_to_text(p.get("description") or "")
        # Append lists section text for skill extraction
        lists = p.get("lists") or []
        for ls in lists:
            body += "\n" + (ls.get("text") or "") + "\n" + html_to_text(ls.get("content") or "")
        body = body[:4000]
        is_remote = detect_remote(location_str, categories.get("commitment") or "", title)
        city, state, coords = parse_location(location_str)
        if is_remote:
            city, state, coords = remote_city_for(job_id_for("lever", sid))
        if not city:
            continue
        lo, hi = extract_salary_range(body)
        out.append(
            NormalizedJob(
                job_id=job_id_for("lever", sid),
                source="lever",
                source_id=sid,
                source_url=p.get("hostedUrl") or p.get("applyUrl") or "",
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
                posted_at=parse_posted_at(p.get("createdAt")),
                is_active=True,
                ingested_at=now,
            )
        )
    return out
