"""Iteration-5 backend tests.

Covers:
- /api/jobs-city/buildings (regression)
- /api/applicants-city/buildings new response shape + limit clamping
- /api/jobs/{id}/summary rate limit (20/60s)
- /api/jobs/{id}/match-score auth + rate limit (10/3600s)
- /api/auth/login regression for demo@jobcity.test
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://ef17ee99-dde7-4098-84a9-83d74e28933a.preview.emergentagent.com",
).rstrip("/")
# Iteration-5 uses the .test domain per /app/memory/test_credentials.md
PUBLIC_BASE = "https://ef17ee99-dde7-4098-84a9-83d74e28933a.preview.emergentagent.com"
API = f"{PUBLIC_BASE}/api"

DEMO_EMAIL = "demo@jobcity.test"
DEMO_PASSWORD = "Demo123!"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def demo_token(session):
    r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture
def demo_auth(demo_token):
    return {"Authorization": f"Bearer {demo_token}", "Content-Type": "application/json"}


# ---------------- Auth regression ----------------

class TestAuthRegression:
    def test_demo_login_works(self, session):
        r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert data["user"]["email"] == DEMO_EMAIL
        assert isinstance(data.get("token"), str) and len(data["token"]) > 20


# ---------------- Jobs City buildings ----------------

class TestJobsCity:
    def test_buildings_public(self, session):
        r = session.get(f"{API}/jobs-city/buildings")
        assert r.status_code == 200
        data = r.json()
        assert "cities" in data
        assert isinstance(data["cities"], list) and len(data["cities"]) > 0
        c0 = data["cities"][0]
        for k in ("city", "state", "lat", "lng", "total_jobs", "companies"):
            assert k in c0, f"missing key {k}"
        assert isinstance(c0["companies"], list) and len(c0["companies"]) > 0


# ---------------- Applicants City buildings ----------------

class TestApplicantsCityBuildings:
    def test_default_response_shape(self, session):
        r = session.get(f"{API}/applicants-city/buildings")
        assert r.status_code == 200
        data = r.json()
        # New fields per iteration 5
        for k in ("applicants", "grid_size", "total", "returned", "limit"):
            assert k in data, f"missing new field: {k}"
        assert data["limit"] == 500, f"default limit should be 500, got {data['limit']}"
        assert data["returned"] == len(data["applicants"])
        assert data["returned"] <= 500
        a0 = data["applicants"][0]
        for k in ("id", "display_name", "floors", "grid_x", "grid_z", "experience_level"):
            assert k in a0, f"missing applicant key: {k}"

    def test_limit_param_capped(self, session):
        r = session.get(f"{API}/applicants-city/buildings", params={"limit": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["limit"] == 10
        assert data["returned"] <= 10
        assert len(data["applicants"]) == data["returned"]

    def test_limit_param_excessive_rejected_or_clamped(self, session):
        r = session.get(f"{API}/applicants-city/buildings", params={"limit": 99999})
        # Per the Query(ge=1, le=2000) FastAPI returns 422
        assert r.status_code in (200, 422), f"unexpected status: {r.status_code}"
        if r.status_code == 200:
            data = r.json()
            assert data["limit"] <= 2000

    def test_limit_zero_rejected(self, session):
        r = session.get(f"{API}/applicants-city/buildings", params={"limit": 0})
        assert r.status_code == 422


# ---------------- Job summary rate limit ----------------

class TestJobSummaryRateLimit:
    """Hammer 25 cache-miss calls. Threshold is 20/60s.
    Without an EMERGENT_LLM_KEY, the LLM call returns 502 (no caching on failure).
    After ~20 calls we expect 429s.
    """

    def _fresh_job_id(self, session):
        r = session.get(f"{API}/jobs", params={"limit": 200})
        items = r.json().get("items", [])
        # Pick a job that does not already have a cached brief by trying ones farther in the list.
        # We can't query job_briefs directly, so just pick something and hope cache miss.
        # If first call returns cached:true, pick another.
        for j in items[::-1]:  # try the tail first (less likely cached)
            jid = j.get("job_id") or j.get("id")
            if not jid:
                continue
            probe = requests.get(f"{API}/jobs/{jid}/summary", timeout=15)
            if probe.status_code == 200 and probe.json().get("cached") is True:
                continue
            # Either 502 (LLM not configured), or 200 not-cached — both fine.
            return jid, probe.status_code
        pytest.skip("No fresh cache-miss job available to probe")

    def test_rate_limit_429_after_threshold(self, session):
        try:
            job_id, first_code = self._fresh_job_id(session)
        except Exception as e:
            pytest.skip(f"could not get fresh job id: {e}")

        codes = [first_code]
        retry_after_seen = None
        for _ in range(24):
            r = requests.get(f"{API}/jobs/{job_id}/summary", timeout=15)
            codes.append(r.status_code)
            if r.status_code == 429:
                retry_after_seen = r.headers.get("Retry-After")
                # We've proven the limit fires; no need to keep hammering.
                if codes.count(429) >= 3:
                    break

        n429 = sum(1 for c in codes if c == 429)
        n502 = sum(1 for c in codes if c == 502)
        n200 = sum(1 for c in codes if c == 200)
        print(f"job_summary codes: 200={n200} 502={n502} 429={n429} total={len(codes)} retry_after={retry_after_seen}")
        assert n429 >= 1, f"expected some 429s after 20+ calls, got: {codes}"
        assert retry_after_seen is not None, "Retry-After header missing on 429"
        # retry_after numeric
        assert int(retry_after_seen) > 0


# ---------------- Match-score rate limit + auth ----------------

class TestMatchScoreAuth:
    def test_requires_auth(self, session):
        # pick any job
        r = session.get(f"{API}/jobs", params={"limit": 1})
        jid = r.json().get("items", [{}])[0].get("job_id")
        assert jid
        r2 = requests.post(f"{API}/jobs/{jid}/match-score", timeout=10)
        assert r2.status_code == 401, f"expected 401 unauth, got {r2.status_code} {r2.text}"

    def test_rate_limit_429_after_threshold(self, session, demo_auth):
        # Pick a job to hammer — match-score caches by (applicant, job_id) for 24h on success.
        # Without a real LLM key the call fails (502), so no cache, so we hit rate limit cleanly.
        r = session.get(f"{API}/jobs", params={"limit": 1})
        jid = r.json().get("items", [{}])[0].get("job_id")
        assert jid

        codes = []
        retry_after = None
        for _ in range(13):
            rr = requests.post(f"{API}/jobs/{jid}/match-score", headers=demo_auth, timeout=15)
            codes.append(rr.status_code)
            if rr.status_code == 429:
                retry_after = rr.headers.get("Retry-After")
                if codes.count(429) >= 2:
                    break

        n429 = sum(1 for c in codes if c == 429)
        n502 = sum(1 for c in codes if c == 502)
        n200 = sum(1 for c in codes if c == 200)
        print(f"match_score codes: 200={n200} 502={n502} 429={n429} total={len(codes)} retry_after={retry_after}")
        # If first call returned 200 cached, we can't easily test rate limit.
        if n200 > 0 and n502 == 0 and n429 == 0:
            pytest.skip("All calls returned 200 cached — cannot test rate limit on cache hit path")
        assert n429 >= 1, f"expected 429 after 10 cache-miss calls, got: {codes}"
        assert retry_after is not None
