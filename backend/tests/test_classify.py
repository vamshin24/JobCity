"""Tests for ingest.classify role categorization."""
from __future__ import annotations

import pytest

from ingest.classify import classify, TECHNICAL_IC


@pytest.mark.parametrize(
    "title,expected",
    [
        # ── software ────────────────────────────────────────────────────────
        ("Software Engineer, Payments", "software"),
        ("Senior Backend Engineer", "software"),
        ("Full-Stack Engineer", "software"),
        ("iOS Engineer", "software"),
        ("Staff Frontend Developer", "software"),
        ("Programmer (Trading Systems)", "software"),
        # ── robotics ────────────────────────────────────────────────────────
        ("Robotics Software Engineer", "robotics"),
        ("Controls Engineer, Locomotion", "robotics"),
        ("Perception Engineer", "robotics"),
        ("Autonomous Vehicle Tech Lead", "robotics"),
        ("SLAM Engineer", "robotics"),
        ("Mechatronics Intern", "robotics"),
        # ── ml ──────────────────────────────────────────────────────────────
        ("Applied Scientist, NLP", "ml"),
        ("Research Engineer, Alignment", "ml"),
        ("Machine Learning Engineer", "ml"),
        ("AI Safety Researcher", "ml"),
        ("Computer Vision Engineer", "ml"),
        # ── data ────────────────────────────────────────────────────────────
        ("Data Engineer, Growth", "data"),
        ("Analytics Engineer", "data"),
        ("Senior Data Scientist", "data"),
        # ── security ────────────────────────────────────────────────────────
        ("Security Engineer", "security"),
        ("Application Security Engineer", "security"),
        ("Red Team Engineer", "security"),
        ("Security Analyst, Bridge", "security"),
        # ── infra ───────────────────────────────────────────────────────────
        ("DevOps Engineer", "infra"),
        ("Site Reliability Engineer", "infra"),
        ("Platform Engineer, Compute", "infra"),
        # ── hardware ────────────────────────────────────────────────────────
        ("ASIC Design Engineer", "hardware"),
        ("Firmware Engineer", "hardware"),
        ("Hardware Engineer, Sensors", "hardware"),
        # ── EXCLUDED: management ────────────────────────────────────────────
        ("Engineering Manager, Platform", "management"),
        ("Director of Engineering", "management"),
        ("VP, Engineering", "management"),
        ("Head of Product", "management"),
        ("CTO", "management"),
        # ── EXCLUDED: product/program ───────────────────────────────────────
        ("Product Manager, Growth", "product"),
        ("Technical Program Manager", "product"),
        ("Senior Product Manager", "product"),
        # ── EXCLUDED: design ────────────────────────────────────────────────
        ("Product Designer", "design"),
        ("Senior UX Designer", "design"),
        # "Design Engineer" without further qualifier → tagged as software
        # (it's a real IC role at Stripe/Vercel etc., we WANT it in the city).
        # ── EXCLUDED: business / GTM ────────────────────────────────────────
        ("Account Executive, Mid-Market", "business"),
        ("Sales Development Representative", "business"),
        ("Customer Success Manager", "business"),
        ("Marketing Operations Specialist", "business"),
        ("Recruiter, Engineering", "business"),
        ("Technical Recruiter", "business"),
        ("Finance Analyst", "business"),
        ("Counsel, Privacy", "business"),
        ("Talent Operations - Program Manager", "business"),
        ("People Project Manager", "business"),
        ("Risk Analyst, Financial Crimes", "business"),
        ("Strategy & Operations Lead", "business"),
        ("Compensation Business Partner", "business"),
        ("Brand Manager", "business"),
        ("Senior Manager, Market Management", "business"),
        # ── Tricky boundary cases ───────────────────────────────────────────
        # "Engineering Manager" must NOT be classified as software just because
        # it contains "engineer".
        ("Engineering Manager", "management"),
        # "Support Engineer" without "engineering" qualifier is GTM at Stripe etc.
        ("Support Engineer", "business"),
    ],
)
def test_classify(title: str, expected: str):
    assert classify(title) == expected


def test_technical_ic_set_excludes_business_management_product():
    assert "software" in TECHNICAL_IC
    assert "robotics" in TECHNICAL_IC
    assert "ml" in TECHNICAL_IC
    assert "data" in TECHNICAL_IC
    assert "security" in TECHNICAL_IC
    assert "infra" in TECHNICAL_IC
    assert "hardware" in TECHNICAL_IC
    # Exclusions
    assert "management" not in TECHNICAL_IC
    assert "product" not in TECHNICAL_IC
    assert "business" not in TECHNICAL_IC
    assert "design" not in TECHNICAL_IC
    assert "other" not in TECHNICAL_IC


def test_classify_empty():
    assert classify("") == "other"
    assert classify(None) == "other"
