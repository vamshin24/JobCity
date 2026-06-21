"""Unit tests for the ingest extract + locations modules.

These run offline — no network — so they're safe in CI.
"""
from __future__ import annotations

import pytest

from ingest.extract import (
    extract_salary_range,
    extract_skills,
    html_to_text,
    infer_level,
    parse_posted_at,
)
from ingest.locations import detect_remote, parse_location


def test_extract_skills_finds_canonical_names():
    text = "Looking for a Senior Python engineer with deep React and PostgreSQL experience. Bonus: K8s, AWS Lambda."
    skills = extract_skills(text)
    # Order is sorted alphabetically
    assert "Python" in skills
    assert "React" in skills
    assert "SQL" in skills  # postgres → SQL canonical
    assert "AWS" in skills
    assert "Kubernetes" in skills
    # Should NOT match "go" inside "google" or similar
    assert "Go" not in skills


def test_extract_skills_word_boundary_protects_short_tokens():
    text = "We use google cloud and golang for the backend."
    skills = extract_skills(text)
    assert "Go" in skills
    assert "GCP" in skills


def test_extract_skills_returns_empty_for_blank():
    assert extract_skills("") == []
    assert extract_skills(None) == []


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Senior Software Engineer", "senior"),
        ("Sr. Backend Engineer", "senior"),
        ("Staff Engineer, ML Platform", "senior"),
        ("Principal Architect", "senior"),
        ("Software Engineering Intern", "entry"),
        ("New Grad Software Engineer", "entry"),
        ("Junior Frontend Developer", "entry"),
        ("Associate Product Manager", "entry"),
        ("Software Engineer", "mid"),
        ("Product Designer", "mid"),
    ],
)
def test_infer_level(title, expected):
    assert infer_level(title) == expected


def test_extract_salary_range_handles_k_suffix():
    text = "Compensation: $120K - $180K plus equity."
    lo, hi = extract_salary_range(text)
    assert lo == 120000
    assert hi == 180000


def test_extract_salary_range_handles_commas():
    text = "Salary range: $145,000 to $210,000 USD."
    lo, hi = extract_salary_range(text)
    assert lo == 145000
    assert hi == 210000


def test_extract_salary_range_missing():
    assert extract_salary_range("No salary listed") == (None, None)


def test_html_to_text_strips_and_collapses():
    s = "<p>Hello&nbsp;<strong>world</strong></p>\n\n<ul><li>One</li><li>Two</li></ul>"
    out = html_to_text(s)
    assert "Hello" in out
    assert "<" not in out
    assert "  " not in out  # collapsed whitespace


def test_html_to_text_truncates():
    out = html_to_text("a" * 5000, max_len=100)
    assert len(out) <= 101  # +1 for ellipsis
    assert out.endswith("…")


def test_parse_posted_at_iso_z():
    s = "2025-10-12T14:23:45Z"
    out = parse_posted_at(s)
    assert out.startswith("2025-10-12")
    assert "+00:00" in out


def test_parse_posted_at_epoch_millis():
    # Lever-style millis: 1697123456000 → 2023-10-12 17:50:56 UTC
    out = parse_posted_at(1697123456000)
    assert out.startswith("2023-10-12")


# ── locations.parse_location ───────────────────────────────────────────────

@pytest.mark.parametrize(
    "raw,expected_city,expected_state",
    [
        ("San Francisco, CA", "San Francisco", "CA"),
        ("San Francisco Bay Area", "San Francisco", "CA"),
        ("NYC", "New York", "NY"),
        ("Brooklyn, NY", "New York", "NY"),
        ("Mountain View, California (Onsite)", "San Jose", "CA"),  # cluster → SJ
        ("Cambridge, MA", "Boston", "MA"),
        ("DC", "Washington", "DC"),
        ("Remote - US", None, None),  # remote with no city → unresolved
    ],
)
def test_parse_location_canonical_matches(raw, expected_city, expected_state):
    city, state, _ = parse_location(raw)
    assert city == expected_city
    assert state == expected_state


def test_detect_remote_keywords():
    assert detect_remote("Remote (US)")
    assert detect_remote("", "Fully remote · WFH")
    assert detect_remote("Distributed Team")
    assert not detect_remote("San Francisco, CA")
    assert not detect_remote("New York, NY")
