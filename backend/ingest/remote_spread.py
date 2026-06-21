"""Deterministic round-robin city assignment for remote jobs.

The ATS pipeline used to plant every remote job at the company HQ's
fallback city. That left whole regions empty AND oversaturated SF/NYC.
Instead, we spread remote jobs evenly across all known US cities by
hashing the job_id — same job_id always → same city across re-ingests.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from data.us_cities import US_CITIES

# Stable, alphabetised list so behaviour is reproducible regardless of
# Python dict insertion order. Sort by (state, city) to interleave coasts.
_CITY_LIST: list[tuple[str, str]] = sorted(US_CITIES.keys(), key=lambda k: (k[1], k[0]))


def remote_city_for(
    job_id: str,
) -> Tuple[str, str, Optional[Tuple[float, float]]]:
    """Pick the (city, state, coords) for a remote job based on hash(job_id).

    Same input → same output every ingest run, so a row that moves from
    "fresh" to "stale" keeps its tower location intact.
    """
    if not job_id:
        # Fallback: still pick a deterministic city instead of dropping.
        job_id = "_jobcity_unknown"
    digest = hashlib.md5(job_id.encode(), usedforsecurity=False).digest()
    bucket = int.from_bytes(digest[:4], "big") % len(_CITY_LIST)
    city, state = _CITY_LIST[bucket]
    return city, state, US_CITIES.get((city, state))
