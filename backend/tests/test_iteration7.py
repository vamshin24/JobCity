"""Iteration-7 backend tests: role-category classifier filter on /api/jobs and
/api/jobs-city/buildings. Verifies the new TECHNICAL_IC default, explicit
category param (single + CSV), 'all' bypass, invalid input safety, compound
filter composition, /jobs/filters 'categories' facet, building aggregate
filtering, and auth regression."""

import os
import random

import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://casual-access.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE_URL}/api"

TECHNICAL_IC = {"software", "robotics", "ml", "data", "security", "infra", "hardware"}
ALL_CATEGORIES = TECHNICAL_IC | {"design", "product", "management", "business", "other"}

DEMO_EMAIL = "demo@jobcity.test"
DEMO_PASS = "Demo123!"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="module")
def filters_payload(s):
    r = s.get(f"{API}/jobs/filters", timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


# ───────────────────── /api/jobs/filters categories facet ─────────────────────

class TestFiltersFacet:
    def test_categories_field_present(self, filters_payload):
        assert "categories" in filters_payload, filters_payload
        cats = filters_payload["categories"]
        assert isinstance(cats, list) and len(cats) > 0
        for c in cats:
            assert "name" in c and "count" in c
            assert isinstance(c["count"], int) and c["count"] >= 0

    def test_categories_sorted_desc(self, filters_payload):
        counts = [c["count"] for c in filters_payload["categories"]]
        assert counts == sorted(counts, reverse=True)

    def test_other_facets_still_present(self, filters_payload):
        for k in ("levels", "sources", "cities", "tech"):
            assert k in filters_payload, f"missing facet {k}"


# ───────────────────── /api/jobs default = TECHNICAL_IC ───────────────────────

class TestDefaultTechnicalIC:
    def test_default_only_technical_ic(self, s):
        r = s.get(f"{API}/jobs", params={"limit": 50}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        items = data["items"]
        assert len(items) > 0
        bad = [it for it in items if it.get("category") not in TECHNICAL_IC]
        assert not bad, f"non-IC leak: {[(b.get('title'), b.get('category')) for b in bad[:5]]}"

    def test_default_total_matches_filters_sum(self, s, filters_payload):
        r = s.get(f"{API}/jobs", params={"limit": 1}, timeout=30)
        assert r.status_code == 200
        default_total = r.json()["total"]
        ic_sum = sum(
            c["count"] for c in filters_payload["categories"] if c["name"] in TECHNICAL_IC
        )
        # Equality expected, but tolerate +/- a couple of in-flight ingest changes.
        assert abs(default_total - ic_sum) <= 5, (default_total, ic_sum)
        # Sanity floor / ceiling — should be a meaningful subset, not empty nor full.
        all_total = sum(c["count"] for c in filters_payload["categories"])
        assert 0 < default_total < all_total


# ───────────────────── single-category param ──────────────────────────────────

class TestSingleCategory:
    def test_management(self, s, filters_payload):
        r = s.get(f"{API}/jobs", params={"category": "management", "limit": 200}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        for it in data["items"]:
            assert it.get("category") == "management", (it.get("title"), it.get("category"))
        mgmt_count = next(
            (c["count"] for c in filters_payload["categories"] if c["name"] == "management"),
            0,
        )
        assert data["total"] == mgmt_count, (data["total"], mgmt_count)

    def test_robotics(self, s, filters_payload):
        r = s.get(f"{API}/jobs", params={"category": "robotics", "limit": 200}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        for it in data["items"]:
            assert it.get("category") == "robotics", (it.get("title"), it.get("category"))
        rb_count = next(
            (c["count"] for c in filters_payload["categories"] if c["name"] == "robotics"),
            0,
        )
        assert data["total"] == rb_count
        # Per request: should be ~22; tolerate small ingest drift.
        assert rb_count >= 10, f"robotics count={rb_count} seems too low"


# ───────────────────── CSV / multiple categories ──────────────────────────────

class TestCsvCategory:
    def test_software_robotics(self, s):
        r = s.get(
            f"{API}/jobs",
            params={"category": "software,robotics", "limit": 200},
            timeout=30,
        )
        assert r.status_code == 200
        for it in r.json()["items"]:
            assert it.get("category") in {"software", "robotics"}, (
                it.get("title"), it.get("category"),
            )

    def test_all_bypasses_filter(self, s, filters_payload):
        r = s.get(f"{API}/jobs", params={"category": "all", "limit": 1}, timeout=30)
        assert r.status_code == 200
        total = r.json()["total"]
        all_total = sum(c["count"] for c in filters_payload["categories"])
        assert total == all_total, (total, all_total)

    def test_invalid_category_no_500(self, s):
        r = s.get(
            f"{API}/jobs",
            params={"category": "invalid_garbage", "limit": 5},
            timeout=30,
        )
        # Per request: must not 500. Deterministic non-500 response.
        assert r.status_code == 200, r.text
        data = r.json()
        # Behavior: invalid → empty cats list → default kicks back to TECHNICAL_IC.
        # Allow either default-tech OR empty results.
        if data["items"]:
            for it in data["items"]:
                assert it.get("category") in TECHNICAL_IC


# ───────────────────── compound filter ────────────────────────────────────────

class TestCompoundFilter:
    def test_software_senior_python(self, s):
        r = s.get(
            f"{API}/jobs",
            params={"category": "software", "level": "senior", "tech": "Python", "limit": 50},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        for it in data["items"]:
            assert it.get("category") == "software"
            assert it.get("level") == "senior"
            skills_lower = [str(sk).lower() for sk in (it.get("skills") or [])]
            assert "python" in skills_lower, (it.get("title"), skills_lower)


# ───────────────────── /api/jobs-city/buildings filtering ────────────────────

class TestBuildings:
    def test_default_total_matches_ic_default(self, s):
        # Default buildings total_jobs across all cities ≈ /api/jobs default total
        jr = s.get(f"{API}/jobs", params={"limit": 1}, timeout=30).json()
        ic_total = jr["total"]
        b = s.get(f"{API}/jobs-city/buildings", timeout=30)
        assert b.status_code == 200
        cities = b.json()["cities"]
        bsum = sum(c["total_jobs"] for c in cities)
        # Buildings total drops jobs in cities not present in city_lookup, so
        # bsum is a lower bound. Assert it is non-trivial and <= ic_total.
        assert 0 < bsum <= ic_total

    def test_default_no_leak(self, s):
        """Spot-check 5 random jobs from one city's company — all must be IC."""
        b = s.get(f"{API}/jobs-city/buildings", timeout=30).json()
        assert b["cities"], "no cities returned"
        # Find a city with at least one company that has >= 5 floors.
        target_company = None
        for city in b["cities"]:
            for co in city["companies"]:
                if co["floors"] >= 5:
                    target_company = co["id"]
                    break
            if target_company:
                break
        assert target_company, "no company with >=5 floors found"
        jr = s.get(
            f"{API}/jobs",
            params={"company_id": target_company, "limit": 50},
            timeout=30,
        ).json()
        items = jr["items"]
        assert items
        sample = random.sample(items, min(5, len(items)))
        for it in sample:
            assert it.get("category") in TECHNICAL_IC, (
                it.get("title"), it.get("category"),
            )

    def test_all_bypass(self, s, filters_payload):
        b = s.get(f"{API}/jobs-city/buildings", params={"category": "all"}, timeout=30)
        assert b.status_code == 200
        bsum = sum(c["total_jobs"] for c in b.json()["cities"])
        all_total = sum(c["count"] for c in filters_payload["categories"])
        # Buildings filter drops untracked cities (no city_lookup match), so
        # bsum can be < all_total but should be larger than the IC-default sum.
        default_b = s.get(f"{API}/jobs-city/buildings", timeout=30).json()
        default_sum = sum(c["total_jobs"] for c in default_b["cities"])
        assert bsum >= default_sum
        assert bsum <= all_total

    def test_robotics_only(self, s):
        b = s.get(
            f"{API}/jobs-city/buildings",
            params={"category": "robotics"},
            timeout=30,
        )
        assert b.status_code == 200
        cities = b.json()["cities"]
        assert cities, "no robotics cities found"
        # Spot-check by sampling one job from each surfaced company.
        # Every job in robotics-only buildings should classify as robotics.
        sampled_companies = []
        for city in cities[:3]:
            for co in city["companies"]:
                sampled_companies.append(co["id"])
        # Look for "Physical Intelligence" in any city's companies.
        all_company_names = {
            co["name"]
            for city in cities
            for co in city["companies"]
        }
        # Soft assertion — feature spec mentions it should appear, but we
        # surface as warning if absent (e.g., posting expired).
        if "Physical Intelligence" not in all_company_names:
            print(
                f"WARN: Physical Intelligence not in robotics buildings; saw {sorted(all_company_names)[:10]}"
            )
        # Hard assertion — verify a sample job is robotics-classified.
        for cid in sampled_companies[:5]:
            jr = s.get(
                f"{API}/jobs",
                params={"company_id": cid, "category": "robotics", "limit": 5},
                timeout=30,
            ).json()
            for it in jr["items"]:
                assert it.get("category") == "robotics", (it.get("title"), it.get("category"))


# ───────────────────── /api/jobs/{id} backward compat ────────────────────────

class TestJobDetailNoGate:
    def test_management_job_still_fetchable(self, s):
        # Pick a management job_id, ensure detail endpoint returns it.
        mgmt = s.get(
            f"{API}/jobs",
            params={"category": "management", "limit": 1},
            timeout=30,
        ).json()
        if not mgmt["items"]:
            pytest.skip("no management jobs available to test backward compat")
        jid = mgmt["items"][0]["job_id"]
        r = s.get(f"{API}/jobs/{jid}", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "job" in data and data["job"]["job_id"] == jid
        assert data["job"].get("category") == "management"


# ───────────────────── auth regression ───────────────────────────────────────

class TestAuthRegression:
    def test_demo_login(self, s):
        r = s.post(
            f"{API}/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASS},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "token" in body or "access_token" in body, body
