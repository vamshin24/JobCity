"""End-to-end tests for the enhanced /api/jobs filters against the real Mongo seed.

Assumes the local ingest has been run at least once (or seeded equivalent).
We test against the live FastAPI app via httpx AsyncClient.
"""
from __future__ import annotations

import httpx
import pytest

BASE = "http://localhost:8001/api"


@pytest.mark.asyncio
async def test_jobs_filters_endpoint_returns_facets():
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(f"{BASE}/jobs/filters")
    assert r.status_code == 200
    data = r.json()
    assert set(data["levels"]).issubset({"entry", "mid", "senior"})
    assert all(s in {"greenhouse", "lever", "ashby", "workable", "recruitee"} for s in data["sources"])
    assert isinstance(data["tech"], list)


@pytest.mark.asyncio
async def test_jobs_level_filter_restricts_results():
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(f"{BASE}/jobs?level=senior&limit=10")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items, "expected at least one senior job in the seed"
    assert all(j["level"] == "senior" for j in items)


@pytest.mark.asyncio
async def test_jobs_tech_filter_or_match():
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(f"{BASE}/jobs?tech=Python,Rust&limit=10")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    for j in items:
        assert {"Python", "Rust"} & set(j.get("skills", []))


@pytest.mark.asyncio
async def test_jobs_role_filter_matches_title_substring():
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(f"{BASE}/jobs?role=Engineer&limit=5")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    assert all("engineer" in j["title"].lower() for j in items)


@pytest.mark.asyncio
async def test_jobs_source_filter():
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(f"{BASE}/jobs?source=ashby&limit=5")
    assert r.status_code == 200
    for j in r.json()["items"]:
        assert j["source"] == "ashby"


@pytest.mark.asyncio
async def test_jobs_posted_within_filter_recent_window():
    async with httpx.AsyncClient(timeout=10.0) as c:
        narrow = await c.get(f"{BASE}/jobs?posted_within=1h&limit=5")
        wide = await c.get(f"{BASE}/jobs?posted_within=30d&limit=5")
    assert narrow.status_code == 200
    assert wide.status_code == 200
    # 30-day window should always be a superset of 1-hour window (or equal)
    assert wide.json()["total"] >= narrow.json()["total"]


@pytest.mark.asyncio
async def test_jobs_compound_filter_role_plus_tech_plus_level():
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(
            f"{BASE}/jobs?role=Engineer&tech=Python&level=senior&limit=5"
        )
    assert r.status_code == 200
    items = r.json()["items"]
    if items:  # compound filter may yield 0 if seed thin
        for j in items:
            assert "engineer" in j["title"].lower()
            assert "Python" in j.get("skills", [])
            assert j["level"] == "senior"
