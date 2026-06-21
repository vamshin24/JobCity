"""Iteration 6 backend regression — real ATS ingest + new /api/jobs filters.

Covers:
- /api/jobs populated by real ATS ingest (no 'seed' source, >1000 jobs, valid sources)
- role / tech / level / posted_within / source filters (single + compound)
- /api/jobs/filters facets endpoint
- /api/jobs/{id} detail still works (job + company)
- /api/jobs-city/buildings real US cities + companies populated
- Auth regression (demo@jobcity.test / Demo123!)
- /api/jobs/{id}/summary rate limit (429 with Retry-After after 20 cache-miss calls)
- APScheduler logs evidence
- CLI `python -m ingest.cli verify` import/connect smoke

All tests hit the public REACT_APP_BACKEND_URL.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://casual-access.preview.emergentagent.com"
).rstrip("/")
API = f"{BASE_URL}/api"

VALID_SOURCES = {"greenhouse", "lever", "ashby", "workable", "recruitee"}


# ---------------- fixtures ----------------

@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="module")
def sample_jobs(s):
    r = s.get(f"{API}/jobs?limit=200", timeout=20)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert items, "/api/jobs returned empty list"
    return items


# ---------------- data shape / ingest ----------------

class TestIngestData:
    def test_total_jobs_above_1000(self, s):
        r = s.get(f"{API}/jobs?limit=1", timeout=20)
        assert r.status_code == 200
        total = r.json()["total"]
        assert total > 1000, f"expected > 1000 jobs, got {total}"

    def test_no_seed_source_and_all_valid(self, s, sample_jobs):
        for j in sample_jobs:
            assert j["source"] != "seed", f"found stale seed job {j.get('job_id')}"
            assert j["source"] in VALID_SOURCES, f"unknown source {j['source']}"

    def test_jobs_have_required_fields(self, sample_jobs):
        for j in sample_jobs[:25]:
            for f in ("job_id", "title", "company_id", "company_name", "source", "is_active"):
                assert f in j, f"missing field {f} in job {j.get('job_id')}"


# ---------------- filters ----------------

class TestFilters:
    def test_role_filter(self, s):
        r = s.get(f"{API}/jobs?role=Engineer&limit=10", timeout=20)
        assert r.status_code == 200
        items = r.json()["items"]
        assert items, "no engineer jobs found"
        for j in items:
            assert "engineer" in j["title"].lower(), j["title"]

    def test_tech_filter_or_semantics(self, s):
        r = s.get(f"{API}/jobs?tech=Python,Rust&limit=10", timeout=20)
        assert r.status_code == 200
        items = r.json()["items"]
        assert items
        for j in items:
            skills_lc = {sk.lower() for sk in j.get("skills", [])}
            assert {"python", "rust"} & skills_lc, f"{j['job_id']} skills={j.get('skills')}"

    @pytest.mark.parametrize("lvl", ["entry", "mid", "senior"])
    def test_level_filter(self, s, lvl):
        r = s.get(f"{API}/jobs?level={lvl}&limit=10", timeout=20)
        assert r.status_code == 200
        items = r.json()["items"]
        assert items, f"no jobs at level={lvl}"
        for j in items:
            assert j["level"] == lvl, f"expected {lvl}, got {j['level']}"

    def test_posted_within_window_subset(self, s):
        wide = s.get(f"{API}/jobs?posted_within=7d&limit=5", timeout=20)
        narrow = s.get(f"{API}/jobs?posted_within=1h&limit=5", timeout=20)
        assert wide.status_code == 200 and narrow.status_code == 200
        wt, nt = wide.json()["total"], narrow.json()["total"]
        # 1h must be subset (<=) of 7d
        assert nt <= wt, f"1h total {nt} should be <= 7d total {wt}"
        assert isinstance(wide.json()["items"], list)

    @pytest.mark.parametrize("src", ["ashby", "greenhouse", "lever"])
    def test_source_filter(self, s, src):
        r = s.get(f"{API}/jobs?source={src}&limit=10", timeout=20)
        assert r.status_code == 200
        items = r.json()["items"]
        assert items, f"no jobs from source={src}"
        for j in items:
            assert j["source"] == src, f"expected {src}, got {j['source']}"

    def test_compound_role_tech_level(self, s):
        r = s.get(
            f"{API}/jobs?role=Engineer&tech=Python&level=senior&limit=5", timeout=20
        )
        assert r.status_code == 200
        items = r.json()["items"]
        # Compound may legitimately be empty for thin slices; if present, every
        # row must satisfy ALL three constraints.
        for j in items:
            assert "engineer" in j["title"].lower()
            skills_lc = {sk.lower() for sk in j.get("skills", [])}
            assert "python" in skills_lc, f"{j['job_id']} skills={j.get('skills')}"
            assert j["level"] == "senior"


# ---------------- facets ----------------

class TestFilterFacets:
    def test_filters_endpoint_shape(self, s):
        r = s.get(f"{API}/jobs/filters", timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ("levels", "sources", "cities", "tech"):
            assert k in d, f"missing key {k}"
        assert set(d["levels"]).issubset({"entry", "mid", "senior"})
        assert d["sources"], "sources empty"
        assert set(d["sources"]).issubset(VALID_SOURCES)
        assert d["cities"] == sorted(d["cities"]), "cities not sorted"
        assert isinstance(d["tech"], list) and d["tech"], "tech empty"
        # Sorted by count desc
        counts = [t["count"] for t in d["tech"]]
        assert counts == sorted(counts, reverse=True), f"tech not desc-sorted: {counts}"
        for t in d["tech"]:
            assert "tag" in t and "count" in t


# ---------------- detail + buildings ----------------

class TestJobDetailAndBuildings:
    def test_job_detail_returns_job_and_company(self, s, sample_jobs):
        jid = sample_jobs[0]["job_id"]
        r = s.get(f"{API}/jobs/{jid}", timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["job"]["job_id"] == jid
        assert d["company"] is not None
        assert d["company"]["company_id"] == sample_jobs[0]["company_id"]

    def test_jobs_city_buildings_has_real_cities(self, s):
        r = s.get(f"{API}/jobs-city/buildings", timeout=30)
        assert r.status_code == 200
        cities = r.json()["cities"]
        assert cities, "no cities returned"
        names = {c["city"] for c in cities}
        # At least one major US tech hub
        assert names & {"San Francisco", "New York", "Seattle", "Austin"}, names
        for c in cities[:5]:
            assert c["total_jobs"] > 0
            assert c["companies"], f"{c['city']} has no companies"
            assert isinstance(c["lat"], (int, float))
            assert isinstance(c["lng"], (int, float))


# ---------------- auth regression ----------------

class TestAuthRegression:
    def test_demo_login_still_works(self, s):
        r = s.post(
            f"{API}/auth/login",
            json={"email": "demo@jobcity.test", "password": "Demo123!"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "token" in d
        assert d["user"]["email"] == "demo@jobcity.test"


# ---------------- rate limit ----------------

class TestRateLimit:
    def test_summary_rate_limit_429_with_retry_after(self, s, sample_jobs):
        jid = sample_jobs[0]["job_id"]
        # EMERGENT_LLM_KEY not configured → expect 502 on each cache-miss; after
        # 20 cache-miss calls the 21st+ should be 429 with Retry-After header.
        statuses = []
        last_resp = None
        for _ in range(25):
            resp = s.get(f"{API}/jobs/{jid}/summary", timeout=15)
            statuses.append(resp.status_code)
            last_resp = resp
            if resp.status_code == 429:
                break
        assert 429 in statuses, f"never got 429 — statuses={statuses}"
        # last_resp is the 429
        assert last_resp.status_code == 429
        ra = last_resp.headers.get("Retry-After")
        assert ra is not None and int(ra) >= 0, f"Retry-After header missing or bad: {ra}"
        # 429 should arrive at or before position 21 (20 cache-miss calls allowed)
        first_429 = statuses.index(429)
        assert first_429 >= 20, f"429 came too early at index {first_429}"


# ---------------- scheduler evidence ----------------

class TestSchedulerLogs:
    def test_scheduler_started_and_ingest_ran(self):
        log = Path("/var/log/supervisor/backend.err.log")
        if not log.exists():
            pytest.skip("backend log not present")
        text = log.read_text(errors="ignore")
        assert "scheduler started" in text, "scheduler-start line missing"
        assert "ingest run finished" in text, "no successful ingest run logged"


# ---------------- CLI smoke ----------------

class TestIngestCli:
    def test_cli_verify_imports_and_connects(self):
        # Run the verify subcommand only — it should not perform a full ingest.
        # If the CLI module fails to import or DB connect, this will fail.
        proc = subprocess.run(
            ["python", "-m", "ingest.cli", "verify"],
            cwd="/app/backend",
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Either it succeeds (exit 0) or it prints a useful message. Treat
        # non-zero as a failure unless it's an ImportError-style. We assert
        # at minimum that it didn't crash with a Python traceback.
        combined = (proc.stdout or "") + (proc.stderr or "")
        assert "Traceback" not in combined, f"CLI crashed:\n{combined}"
        # And the process exited cleanly
        assert proc.returncode == 0, f"verify exit={proc.returncode}\n{combined}"
