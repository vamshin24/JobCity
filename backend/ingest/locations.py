"""City normalization + lat/lng lookup for ingested job locations.

ATS responses give us free-text location strings like "San Francisco, CA",
"NYC", "New York City", "Remote - US", "Greater Boston Area". We need to
map them to one of our known US cities (data/us_cities.py) or mark `remote`.

Strategy: regex extract city/state, normalize via aliases, look up coords.
If nothing matches → return (None, None, None) and the caller decides.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

from data.us_cities import US_CITIES

# (city_norm) → (city_canonical, state)
_CITY_ALIASES = {
    "nyc": ("New York", "NY"),
    "new york city": ("New York", "NY"),
    "new york": ("New York", "NY"),
    "manhattan": ("New York", "NY"),
    "brooklyn": ("New York", "NY"),
    "sf": ("San Francisco", "CA"),
    "san francisco bay area": ("San Francisco", "CA"),
    "bay area": ("San Francisco", "CA"),
    "the bay area": ("San Francisco", "CA"),
    "sfo": ("San Francisco", "CA"),
    "san francisco": ("San Francisco", "CA"),
    "south san francisco": ("San Francisco", "CA"),
    "mountain view": ("San Jose", "CA"),
    "palo alto": ("San Jose", "CA"),
    "menlo park": ("San Jose", "CA"),
    "santa clara": ("San Jose", "CA"),
    "sunnyvale": ("San Jose", "CA"),
    "redwood city": ("San Jose", "CA"),
    "cupertino": ("San Jose", "CA"),
    "san jose": ("San Jose", "CA"),
    "oakland": ("San Francisco", "CA"),
    "berkeley": ("San Francisco", "CA"),
    "la": ("Los Angeles", "CA"),
    "los angeles": ("Los Angeles", "CA"),
    "santa monica": ("Los Angeles", "CA"),
    "venice": ("Los Angeles", "CA"),
    "hollywood": ("Los Angeles", "CA"),
    "culver city": ("Los Angeles", "CA"),
    "san diego": ("San Diego", "CA"),
    "seattle": ("Seattle", "WA"),
    "redmond": ("Seattle", "WA"),
    "bellevue": ("Seattle", "WA"),
    "kirkland": ("Seattle", "WA"),
    "portland": ("Portland", "OR"),
    "austin": ("Austin", "TX"),
    "dallas": ("Dallas", "TX"),
    "dfw": ("Dallas", "TX"),
    "fort worth": ("Dallas", "TX"),
    "houston": ("Houston", "TX"),
    "denver": ("Denver", "CO"),
    "boulder": ("Denver", "CO"),
    "salt lake city": ("Salt Lake City", "UT"),
    "slc": ("Salt Lake City", "UT"),
    "phoenix": ("Phoenix", "AZ"),
    "scottsdale": ("Phoenix", "AZ"),
    "tempe": ("Phoenix", "AZ"),
    "las vegas": ("Las Vegas", "NV"),
    "atlanta": ("Atlanta", "GA"),
    "miami": ("Miami", "FL"),
    "orlando": ("Orlando", "FL"),
    "chicago": ("Chicago", "IL"),
    "detroit": ("Detroit", "MI"),
    "ann arbor": ("Detroit", "MI"),
    "minneapolis": ("Minneapolis", "MN"),
    "st. paul": ("Minneapolis", "MN"),
    "st louis": ("St. Louis", "MO"),
    "st. louis": ("St. Louis", "MO"),
    "saint louis": ("St. Louis", "MO"),
    "nashville": ("Nashville", "TN"),
    "charlotte": ("Charlotte", "NC"),
    "raleigh": ("Raleigh", "NC"),
    "durham": ("Raleigh", "NC"),
    "rtp": ("Raleigh", "NC"),
    "washington": ("Washington", "DC"),
    "washington dc": ("Washington", "DC"),
    "dc": ("Washington", "DC"),
    "arlington": ("Washington", "DC"),
    "alexandria": ("Washington", "DC"),
    "philadelphia": ("Philadelphia", "PA"),
    "philly": ("Philadelphia", "PA"),
    "new york ny": ("New York", "NY"),
    "boston": ("Boston", "MA"),
    "cambridge": ("Boston", "MA"),
    "pittsburgh": ("Pittsburgh", "PA"),
    "columbus": ("Columbus", "OH"),
    "indianapolis": ("Indianapolis", "IN"),
}

_REMOTE_TOKENS = (
    "remote",
    "anywhere",
    "wfh",
    "work from home",
    "distributed",
    "virtual",
    "fully remote",
    "remote first",
    "remote-first",
)


def _norm(s: str) -> str:
    return re.sub(r"[\s\-_/,]+", " ", s).strip().lower()


def detect_remote(*texts: str) -> bool:
    for t in texts:
        if not t:
            continue
        n = _norm(t)
        if any(tok in n for tok in _REMOTE_TOKENS):
            return True
    return False


def parse_location(location: str) -> Tuple[Optional[str], Optional[str], Optional[Tuple[float, float]]]:
    """Return (city, state, (lat, lng)) or (None, None, None) if unresolved.

    Strips parenthetical metadata, splits on common separators, walks fragments
    from most-specific to least-specific.
    """
    if not location:
        return (None, None, None)

    text = re.sub(r"\([^)]*\)", " ", location)  # drop "(US)" "(remote ok)" etc.
    text = re.sub(r"\b(usa?|united states|us-only|on-?site)\b", " ", text, flags=re.I)

    # Try the whole string + common fragment shapes
    candidates = [text]
    candidates += re.split(r"[;|/]| or |,| - ", text, flags=re.I)
    candidates += text.split()  # last-ditch single-word matches

    for frag in candidates:
        n = _norm(frag)
        if not n:
            continue
        # Exact alias hit?
        if n in _CITY_ALIASES:
            city, state = _CITY_ALIASES[n]
            coords = US_CITIES.get((city, state))
            return (city, state, coords)
        # "city, state" pattern, e.g. "New York, NY"
        m = re.match(r"^([a-z .]+?)\s+([a-z]{2})$", n)
        if m:
            n2 = m.group(1).strip()
            if n2 in _CITY_ALIASES:
                city, state = _CITY_ALIASES[n2]
                return (city, state, US_CITIES.get((city, state)))

    return (None, None, None)
