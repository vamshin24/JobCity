"""Curated company → ATS board slug map.

Each entry: source (greenhouse|lever|ashby|workable|recruitee), slug, display name,
optional brand color, optional fallback HQ city for "Remote" jobs.

This file is intentionally hand-curated and grows via PR. Contributors:
- Pick a company that uses one of the supported ATSes
- Find their public job board URL (it usually contains the slug)
- Append below. Run `python -m ingest.cli verify` to sanity-check the slug.
"""

# Brand hexes (kept short — the 3D scene varies them per-city anyway)
_BLUE = "#5B8DEF"
_GREEN = "#3DDC97"
_RED = "#FF5F6D"
_AMBER = "#FFB24C"
_PURPLE = "#A78BFA"
_PINK = "#F472B6"
_CYAN = "#00FFCC"
_LIME = "#A3E635"

COMPANIES = [
    # ── Greenhouse ──────────────────────────────────────────────────────────
    {"source": "greenhouse", "slug": "airbnb",        "name": "Airbnb",        "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "stripe",        "name": "Stripe",        "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "anthropic",     "name": "Anthropic",     "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "openai",        "name": "OpenAI",        "color": _GREEN,  "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "robinhood",     "name": "Robinhood",     "color": _LIME,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "reddit",        "name": "Reddit",        "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "coinbase",      "name": "Coinbase",      "color": _BLUE,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "doordash",      "name": "DoorDash",      "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "instacart",     "name": "Instacart",     "color": _GREEN,  "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "lyft",          "name": "Lyft",          "color": _PINK,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "pinterest",     "name": "Pinterest",     "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "squarespace",   "name": "Squarespace",   "color": "#FFFFFF", "fallback_city": "New York"},
    {"source": "greenhouse", "slug": "twitch",        "name": "Twitch",        "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "twilio",        "name": "Twilio",        "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "asana",         "name": "Asana",         "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "affirm",        "name": "Affirm",        "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "brex",          "name": "Brex",          "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "datadog",       "name": "Datadog",       "color": _PURPLE, "fallback_city": "New York"},
    {"source": "greenhouse", "slug": "plaid",         "name": "Plaid",         "color": _BLUE,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "roblox",        "name": "Roblox",        "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "discord",       "name": "Discord",       "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "block",         "name": "Block",         "color": _CYAN,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "webflow",       "name": "Webflow",       "color": _BLUE,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "figma",         "name": "Figma",         "color": _GREEN,  "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "duolingo",      "name": "Duolingo",      "color": _GREEN,  "fallback_city": "Pittsburgh"},
    {"source": "greenhouse", "slug": "dropbox",       "name": "Dropbox",       "color": _BLUE,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "rippling",      "name": "Rippling",      "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "snap",          "name": "Snap",          "color": _AMBER,  "fallback_city": "Los Angeles"},
    {"source": "greenhouse", "slug": "wayfair",       "name": "Wayfair",       "color": _PURPLE, "fallback_city": "Boston"},
    {"source": "greenhouse", "slug": "yelp",          "name": "Yelp",          "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "1password",     "name": "1Password",     "color": _BLUE,   "fallback_city": "Toronto"},
    {"source": "greenhouse", "slug": "carta",         "name": "Carta",         "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "checkr",        "name": "Checkr",        "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "scaleai",       "name": "Scale AI",      "color": _BLUE,   "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "samsara",       "name": "Samsara",       "color": _BLUE,   "fallback_city": "San Francisco"},

    # ── Lever ───────────────────────────────────────────────────────────────
    {"source": "lever", "slug": "netflix",      "name": "Netflix",       "color": _RED,    "fallback_city": "Los Angeles"},
    {"source": "lever", "slug": "lever",        "name": "Lever",         "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "lever", "slug": "posthog",      "name": "PostHog",       "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "lever", "slug": "spotify",      "name": "Spotify",       "color": _GREEN,  "fallback_city": "New York"},
    {"source": "lever", "slug": "ridgelinellc", "name": "Ridgeline",     "color": _BLUE,   "fallback_city": "New York"},
    {"source": "lever", "slug": "fanduel",      "name": "FanDuel",       "color": _BLUE,   "fallback_city": "New York"},
    {"source": "lever", "slug": "highspot",     "name": "Highspot",      "color": _RED,    "fallback_city": "Seattle"},
    {"source": "lever", "slug": "shopify",      "name": "Shopify",       "color": _GREEN,  "fallback_city": "Toronto"},
    {"source": "lever", "slug": "wave",         "name": "Wave",          "color": _BLUE,   "fallback_city": "Toronto"},
    {"source": "lever", "slug": "kraken",       "name": "Kraken",        "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "lever", "slug": "writer",       "name": "Writer",        "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "lever", "slug": "matterport",   "name": "Matterport",    "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "lever", "slug": "mux",          "name": "Mux",           "color": _CYAN,   "fallback_city": "San Francisco"},
    {"source": "lever", "slug": "attentive",    "name": "Attentive",     "color": _PINK,   "fallback_city": "New York"},
    {"source": "lever", "slug": "celonis",      "name": "Celonis",       "color": _PURPLE, "fallback_city": "New York"},

    # ── Ashby ───────────────────────────────────────────────────────────────
    {"source": "ashby", "slug": "linear",      "name": "Linear",       "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "vercel",      "name": "Vercel",       "color": "#FFFFFF", "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "ramp",        "name": "Ramp",         "color": _AMBER,  "fallback_city": "New York"},
    {"source": "ashby", "slug": "mercury",     "name": "Mercury",      "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "notion",      "name": "Notion",       "color": "#FFFFFF", "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "loom",        "name": "Loom",         "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "replit",      "name": "Replit",       "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "cursor",      "name": "Cursor",       "color": "#FFFFFF", "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "raycast",     "name": "Raycast",      "color": _RED,    "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "supabase",    "name": "Supabase",     "color": _GREEN,  "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "perplexity",  "name": "Perplexity",   "color": _CYAN,   "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "deel",        "name": "Deel",         "color": _PURPLE, "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "elevenlabs",  "name": "ElevenLabs",   "color": _RED,    "fallback_city": "New York"},
    {"source": "ashby", "slug": "browserbase", "name": "Browserbase",  "color": _AMBER,  "fallback_city": "San Francisco"},
    {"source": "ashby", "slug": "modal",       "name": "Modal",        "color": _LIME,   "fallback_city": "New York"},

    # ── Workable ────────────────────────────────────────────────────────────
    {"source": "workable", "slug": "deepl",        "name": "DeepL",          "color": _BLUE,  "fallback_city": "New York"},
    {"source": "workable", "slug": "remote",       "name": "Remote.com",     "color": _GREEN, "fallback_city": "San Francisco"},
    {"source": "workable", "slug": "circleci",     "name": "CircleCI",       "color": _BLUE,  "fallback_city": "San Francisco"},
    {"source": "workable", "slug": "bigcommerce",  "name": "BigCommerce",    "color": _BLUE,  "fallback_city": "Austin"},

    # ── Recruitee ───────────────────────────────────────────────────────────
    {"source": "recruitee", "slug": "tidio",       "name": "Tidio",          "color": _BLUE,  "fallback_city": "New York"},
    {"source": "recruitee", "slug": "infermedica", "name": "Infermedica",    "color": _CYAN,  "fallback_city": "Boston"},

    # ── Robotics & autonomy companies ───────────────────────────────────────
    {"source": "greenhouse", "slug": "nuro",                   "name": "Nuro",                  "color": _RED,      "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "wing",                   "name": "Wing",                  "color": _LIME,     "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "waymo",                  "name": "Waymo",                 "color": _BLUE,     "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "aurorainnovation",       "name": "Aurora",                "color": _GREEN,    "fallback_city": "Pittsburgh"},
    {"source": "greenhouse", "slug": "wayve",                  "name": "Wayve",                 "color": _CYAN,     "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "neuralink",              "name": "Neuralink",             "color": "#FFFFFF", "fallback_city": "San Francisco"},
    {"source": "greenhouse", "slug": "diligentrobotics",       "name": "Diligent Robotics",     "color": _PURPLE,   "fallback_city": "Austin"},
    {"source": "greenhouse", "slug": "locusrobotics",          "name": "Locus Robotics",        "color": _AMBER,    "fallback_city": "Boston"},
    {"source": "greenhouse", "slug": "outrider",               "name": "Outrider",              "color": _BLUE,     "fallback_city": "Denver"},
    {"source": "lever",      "slug": "zoox",                   "name": "Zoox",                  "color": _PINK,     "fallback_city": "San Francisco"},
    {"source": "lever",      "slug": "dexterity",              "name": "Dexterity",             "color": _AMBER,    "fallback_city": "San Francisco"},
    {"source": "lever",      "slug": "saronic",                "name": "Saronic",               "color": _BLUE,     "fallback_city": "Austin"},
    {"source": "ashby",      "slug": "1x",                     "name": "1X Technologies",       "color": _PURPLE,   "fallback_city": "San Francisco"},
    {"source": "ashby",      "slug": "physicalintelligence",   "name": "Physical Intelligence", "color": _CYAN,     "fallback_city": "San Francisco"},
    {"source": "ashby",      "slug": "figure",                 "name": "Figure",                "color": "#FFFFFF", "fallback_city": "San Francisco"},
]
