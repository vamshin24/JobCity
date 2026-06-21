"""Tech-stack / level / posted-date extraction from raw ATS payloads.

Pure regex/keyword matching — no LLM, no network. Fast and deterministic so
the ingest cron can keep up.
"""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Tuple

# ── tech stack lexicon ────────────────────────────────────────────────────────
# Each entry: (canonical_name, [aliases or regex_phrases (case-insensitive)])
# Aliases that contain a non-word character are treated as literal substrings;
# otherwise we wrap them in \b…\b so "go" doesn't match "google".
_TECH_LEXICON: List[Tuple[str, List[str]]] = [
    ("Python", ["python", "py3", "django", "flask", "fastapi", "pytorch", "tensorflow", "numpy", "pandas"]),
    ("JavaScript", ["javascript", "js", "es6"]),
    ("TypeScript", ["typescript", "ts"]),
    ("React", ["react", "react.js", "reactjs", "next.js", "nextjs"]),
    ("Vue", ["vue", "vue.js", "vuejs", "nuxt"]),
    ("Angular", ["angular", "angularjs"]),
    ("Svelte", ["svelte", "sveltekit"]),
    ("Node.js", ["node", "node.js", "nodejs", "express", "nestjs"]),
    ("Go", ["golang", "go lang"]),
    ("Rust", ["rust"]),
    ("Java", ["java", "spring boot", "spring framework"]),
    ("Kotlin", ["kotlin"]),
    ("Swift", ["swift", "swiftui"]),
    ("Objective-C", ["objective-c", "objective c"]),
    ("C++", ["c++", "cpp"]),
    ("C#", ["c#", ".net", "dotnet", "asp.net"]),
    ("Ruby", ["ruby", "ruby on rails", "rails"]),
    ("PHP", ["php", "laravel", "symfony"]),
    ("Scala", ["scala"]),
    ("Elixir", ["elixir", "phoenix framework"]),
    ("R", ["r language", "r programming"]),
    ("MATLAB", ["matlab"]),
    ("SQL", ["sql", "postgresql", "postgres", "mysql", "mariadb", "sqlite", "mssql", "tsql"]),
    ("NoSQL", ["nosql", "mongodb", "dynamodb", "couchdb", "cassandra"]),
    ("Redis", ["redis"]),
    ("Kafka", ["kafka"]),
    ("Spark", ["apache spark", "pyspark"]),
    ("Airflow", ["airflow"]),
    ("dbt", ["dbt"]),
    ("Snowflake", ["snowflake"]),
    ("BigQuery", ["bigquery", "big query"]),
    ("Databricks", ["databricks"]),
    ("AWS", ["aws", "amazon web services", "ec2", "lambda", "s3", "dynamo"]),
    ("GCP", ["gcp", "google cloud"]),
    ("Azure", ["azure", "microsoft azure"]),
    ("Kubernetes", ["kubernetes", "k8s", "eks", "gke", "aks"]),
    ("Docker", ["docker", "containers"]),
    ("Terraform", ["terraform", "iac"]),
    ("GraphQL", ["graphql", "apollo"]),
    ("REST", ["rest api", "restful", "openapi"]),
    ("gRPC", ["grpc", "protobuf"]),
    ("ML", ["machine learning", "deep learning", "nlp", "llm", "transformer", "transformers"]),
    ("LLMs", ["llms", "rag", "retrieval augmented", "openai api", "anthropic", "claude", "gemini"]),
    ("PyTorch", ["pytorch", "torch"]),
    ("TensorFlow", ["tensorflow", "tf2"]),
    ("CUDA", ["cuda", "gpu"]),
    ("iOS", ["ios", "iphone", "ipad"]),
    ("Android", ["android"]),
    ("Flutter", ["flutter", "dart"]),
    ("React Native", ["react native"]),
    ("Tailwind", ["tailwind", "tailwindcss"]),
    ("WebGL", ["webgl", "three.js", "threejs"]),
    ("Solidity", ["solidity", "smart contracts"]),
    ("Blockchain", ["blockchain", "web3", "ethereum"]),
]


def _compile_lexicon():
    compiled = []
    for canon, aliases in _TECH_LEXICON:
        patterns = []
        for a in aliases:
            if re.search(r"[^a-z0-9]", a, flags=re.I):
                # contains punctuation/space — escape and use as literal substring
                patterns.append(re.escape(a))
            else:
                patterns.append(rf"\b{re.escape(a)}\b")
        compiled.append((canon, re.compile("|".join(patterns), re.I)))
    return compiled


_COMPILED_TECH = _compile_lexicon()


def extract_skills(text: str) -> List[str]:
    """Return a sorted, de-duplicated list of canonical tech names found in `text`."""
    if not text:
        return []
    hits = set()
    for canon, pattern in _COMPILED_TECH:
        if pattern.search(text):
            hits.add(canon)
    return sorted(hits)


# ── seniority/level inference ──────────────────────────────────────────────
_LEVEL_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("senior",   re.compile(r"\b(staff|principal|lead|sr\.?|senior|architect|fellow|director|head of)\b", re.I)),
    ("entry",    re.compile(r"\b(intern|internship|new ?grad|new ?graduate|entry[- ]?level|junior|jr\.?|early career|early-career|associate|university grad)\b", re.I)),
]


def infer_level(title: str, body: str = "") -> str:
    """Return one of: entry | mid | senior. Defaults to 'mid' if nothing matches."""
    title = title or ""
    body = body or ""
    # Title wins
    for level, pat in _LEVEL_PATTERNS:
        if pat.search(title):
            return level
    for level, pat in _LEVEL_PATTERNS:
        if pat.search(body):
            return level
    return "mid"


# ── salary parsing ─────────────────────────────────────────────────────────
_SALARY_PAIR = re.compile(
    r"\$\s?(\d{2,3}(?:[,.]\d{3})?(?:[,.]\d{3})?|\d{2,3}k?)\s*[-–to]+\s*\$?\s?(\d{2,3}(?:[,.]\d{3})?(?:[,.]\d{3})?|\d{2,3}k?)",
    re.I,
)


def _parse_money_token(tok: str) -> Optional[int]:
    t = tok.lower().replace(",", "").replace(".", "").replace("$", "").strip()
    if not t:
        return None
    if t.endswith("k"):
        try:
            return int(float(t[:-1]) * 1000)
        except ValueError:
            return None
    try:
        n = int(t)
    except ValueError:
        return None
    if n < 1000:  # almost certainly "120" meaning 120k
        n *= 1000
    return n


def extract_salary_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    if not text:
        return (None, None)
    m = _SALARY_PAIR.search(text)
    if not m:
        return (None, None)
    lo = _parse_money_token(m.group(1))
    hi = _parse_money_token(m.group(2))
    if lo and hi and lo > hi:
        lo, hi = hi, lo
    return (lo, hi)


# ── description sanitization ───────────────────────────────────────────────
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def html_to_text(s: str, max_len: int = 4000) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = _TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip() + "…"
    return s


# ── posted_at parsing ──────────────────────────────────────────────────────
def parse_posted_at(value) -> str:
    """Coerce various ATS timestamp formats to ISO-8601 UTC string."""
    if not value:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, (int, float)):
        # millis or seconds? Lever uses millis epochs.
        n = float(value)
        if n > 1e12:
            n /= 1000.0
        try:
            return datetime.fromtimestamp(n, tz=timezone.utc).isoformat()
        except (OSError, ValueError):
            return datetime.now(timezone.utc).isoformat()
    s = str(value)
    # Try common ISO-ish shapes
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s.replace("Z", "+0000") if fmt.endswith("%z") else s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()
