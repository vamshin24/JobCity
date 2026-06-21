# JobCity — PRD (living)

## Original problem statement (verbatim)

> Using emergent I want to build a map with 2 cities one for Job applicants and one for companies where applicants can apply, this idea is something similar to https://www.thegitcity.com/ AND THEIR GITHUB https://github.com/srizzon/git-city where every building represents a git account/user and the number of recent commits they've done and can compare with other git users on number of commits. Similarly I want applicants city where buildings represent applicants and stats like how many jobs they've applied in job's city (with companies). The jobs city should be like USA Map with company buildings representing according to the location on job description which will be taken (either scrapping or API endpoints) from jobright, indeed, linkedin, simplify, yc, built-in spread out according to location and company name. (For example if Amazon has posted 10 jobs in Seattle, LA, SF, Atlanta, with 2, 3, 2, 3 jobs respectively, then Seattle should have a building named Amazon with 2 floors because 2 jobs in Seattle, and LA should have building of Amazon with 3 floors.)

## User-confirmed choices (Feb 2026)
- MVP scope: both cities (Jobs City richer)
- Auth: JWT email/password + Emergent Google login
- Job data: **real ingestion in MVP** (RemoteOK + Greenhouse public boards) on top of seeded data
- Aesthetic: low-poly dusk for Jobs City, cyberpunk-night for Applicants City
- Push to GitHub: user will use Emergent "Push to GitHub" button after build

## Architecture
- React 19 + React Three Fiber + drei + three.js (3D)
- FastAPI (async) + Motor (Mongo) + PyJWT + bcrypt
- MongoDB collections: users, applicants, companies, jobs, applications, user_sessions
- Auth: JWT (cookies + Bearer parallel), with Emergent Google session bridge
- Data ingestion: `services/ingestion.py` (RemoteOK feed + Greenhouse public boards)

## Personas
1. **Sam the Applicant** — recent grad, exploring & applying.
2. **Priya the Power Applicant** — wants comparison vs peers.
3. **Visitor (no account)** — explores cities, prompted to sign up at apply.

## Routes
- `/` Landing (dual-CTA)
- `/jobs-city` 3D Jobs City
- `/applicants-city` 3D Applicants City
- `/jobs/:id` Job detail + Apply
- `/applicants/:id` Applicant profile
- `/profile` (auth) My applications & building
- `/compare` Side-by-side comparison
- `/login`, `/register`

## What's been implemented (through Feb 14, 2026 — iterations 1–3)
- ✅ JWT email/password auth + Emergent Google session bridge
- ✅ MongoDB models with UUID `user_id` (no ObjectId leakage), unique indexes
- ✅ Seed script: 20 companies, ~404 templated jobs, 30 demo applicants, demo applications, admin + demo accounts
- ✅ Real data ingestion: **RemoteOK + Greenhouse + Lever + YC/HN**, server-side **filter to Software/ML/Robotics only** (`services/job_filter.py`); ~763 active jobs split 118 software / 55 ML / 27 robotics across 38 companies. Auto-refresh every 6h.
- ✅ Aggregation endpoints: `/api/jobs-city/buildings` and `/api/applicants-city/buildings`
- ✅ 3D Jobs City — **sqrt-scaled building heights** (no more 167-floor monoliths), **procedural window textures on every building** (Canvas-generated, lit/unlit grid), **point-light glow on hover & selection**, InstancedMesh path for short buildings, multi-tier skyscrapers with spires for tall ones, search-bar dim
- ✅ 3D Applicants City — same windows + glow + sqrt scaling, neon experience-level palette, GitHub antennas, skyscrapers for power users, search-bar dim by name/level/github
- ✅ Apply flow with duplicate prevention, cover note, toast feedback
- ✅ AI match score on `/jobs/:id` — Claude Sonnet 4.5 via Emergent LLM key, 24h cache
- ✅ GitHub link on `/profile` — paste a username, public events API counts last-30-day commits and updates the antenna
- ✅ Profile page with my-building link, GitHub form, stat tiles, applications list
- ✅ Compare page with bar charts and top-companies stats
- ✅ Landing page with dual-image hero, glass-morphism, Unbounded + Outfit + JetBrains Mono fonts
- ✅ NavBar with sign-in/out/profile links
- ✅ r3f patched to ignore `x-*` JSX props injected by visual-edits babel plugin
- ✅ Deployment health check: PASS
- ✅ Testing agent runs: **iter_1 (14/14 + e2e)**, **iter_2 (25/25 + e2e)**, **iter_3 (7/7 skyscraper + search e2e)** — all green

## Iteration 4 — Feb 15, 2026 (this session)
- ✅ Restored missing `.env` files (backend + frontend) after fork, added `.env.example` templates
- ✅ JobDetail UX overhaul: AI brief (summary + required/nice-to-have skills) auto-loads on mount; "Score me" button removed; external Apply opens job portal in new tab; "Did you apply?" `AlertDialog` triggers on tab return via `visibilitychange` + `focus` listeners; seed jobs without `source_url` skip new-tab and open dialog directly
- ✅ New `ApplicantRoads` component: horizontal + vertical asphalt strips with cyan neon center stripes form a grid between applicant towers (24×24, spacing 2.4)
- ✅ Emergent LLM Key wired in — `/api/jobs/{id}/summary` and `/api/jobs/{id}/match-score` confirmed live with Claude Sonnet 4.5
- ✅ Login.jsx defaults aligned with seed (`demo@jobcity.test` / `Demo123!`)
- ✅ Visually verified via screenshot tool (frontend testing agent struggles with WebGL canvases)

## Iteration 5 — Feb 15, 2026 (this session continued)
- ✅ **CORS fix**: switched API axios client to `withCredentials: false` so Cloudflare's `Access-Control-Allow-Origin: *` override no longer breaks credentials-mode preflight in Emergent preview. Auth still works via Bearer token in localStorage.
- ✅ **Applicants City revamp** — Sheet drawer side panel replaces nav to `/applicants/:id`; shows title, applications count, skills, GitHub stats, and clickable resume link only (no jobs list)
- ✅ **Compare flow** — click = open side panel (focus glow only, no auto-select). "+ Add to compare" button in the side panel stacks up to 4 applicants; floating dock at the bottom shows chips with remove-X + "Compare side-by-side →" CTA
- ✅ **Navigate to my tower** — top-right CTA visible only when logged in. Smoothly tweens camera + orbit-controls target to the user's building (ease-out cubic over ~1.25s) and opens its side panel.
- ✅ **New `/onboarding` page** — collected after register: title (with suggestion chips), experience level toggle, skills (chip multi-input), resume URL. All fields optional with "Skip for now". Backed by `PATCH /api/applicants/me`.
- ✅ Register flow now redirects to `/onboarding` instead of `/profile`.
- ✅ **Visual overhaul** of Applicants City to match the user's "pixelated lo-fi green night-city" reference (background `#091a12`, `NearestFilter` pixel windows, bright APPLICANT_CITY_COLORS palette).
- ✅ Backend `PATCH /api/applicants/me` endpoint accepts `title`, `headline`, `skills`, `resume_url`, `experience_level`.
- ✅ Applicants schema gains `title` and `resume_url` (both optional).
- ✅ `/api/applicants-city/buildings` response now includes `title` so it shows on hover tooltip + side panel.

## Iteration 6 — Feb 15, 2026 (gitcity-style focus)
- ✅ **Building grid collision fix** — `/api/applicants-city/buildings` now sorts by applications desc and uses a deterministic spiral walk to push duplicates to the nearest empty slot. Verified 32/32 unique slots in the seeded city.
- ✅ **Removed antenna/spire lines** from both cities — Skyscraper.jsx no longer renders the cylinder spire; ApplicantBuildings.jsx no longer renders GitHub antennas.
- ✅ **Click building → camera zoom + golden focus beam** — selecting a tower now triggers a "close" camera fly (offset `[+4, 8, +6]`), drops a tall pulsing yellow beam through the focused building with a spinning octahedral diamond marker on top and a ground halo. Surrounding regular towers fade to ~55% opacity (solo-mode), and skyscrapers dim via the existing dim path.
- ✅ **Profile card redesign** (gitcity-inspired) — radial avatar, @handle, title, level letter (S/A/B) with linear gradient progress bar, role + GitHub tags, 3×2 stat grid (APPS · COMMITS/30D · SKILLS · LEVEL · STATUS · HIRABLE), skills chips, VIEW RESUME (gold), + COMPARE, GITHUB ↗ buttons.
- ✅ **Search → fly-to-applicant** — pressing Enter in the search box matches the first applicant by name/title/level/github; on match: success toast + camera fly + focus panel; on no match: error toast "No applicant found matching X.".

## Iteration 7 — Jun 15, 2026 (guest-friendly entry)
- ✅ **Removed forced-login redirect for guests** — `lib/authToken.js` 401 interceptor now only bounces to `/login?expired=1` when a token actually existed (session expiry). Anonymous probes from `AuthProvider`'s `/auth/me` on first load no longer kick guests off `/`, `/register`, `/jobs-city`, etc.
- ✅ **Login page** — added a top-right `X` close button (`login-guest-close-btn`) and a `Skip — continue as guest →` link (`login-continue-as-guest-btn`) below the form. Both navigate to `/`.
- ✅ **Register page** — same X close (`register-guest-close-btn`) and `Skip — continue as guest →` link (`register-continue-as-guest-btn`).

## Iteration 8 — Jun 20, 2026 (Bucket A + D + B + C)

### Bucket A — Quick UX cleanups
- ✅ **Removed "My Tower"** from NavBar (only Jobs City / Applicants City / Edit profile remain)
- ✅ **Hide GitHub button** in ApplicantSidePanel when applicant has no real `github_username` (the fallback handle that produced 404 links is gone). New testid: `applicant-github-link`.
- ✅ **Clear search input** after Enter→fly on Applicants City
- ✅ Sheet → div migration on Applicants City confirmed (no dead Sheet import remained)

### Bucket D — Jobs City parity with Applicants City
- ✅ **Focus beam + halo + spinning diamond** marker over the selected company tower (`CompanyBuildings.FocusBeam`, golden #FFD23F, same pattern as Applicants)
- ✅ **Smooth solo-mode dim** of non-selected company towers via lerped material opacity (`useFrame` on `matSoloRef`)
- ✅ **Search-on-Enter fly-to-company** — pressing Enter in the Jobs City search box matches by company/city/state, sets selected + flyTarget, opens the side panel
- ✅ **Camera fly + auto-rotate** — new `CameraFly` component in `JobsCityScene.jsx` mirrors the Applicants City fly logic (close/medium offsets, cubic ease, target+position lerp). Auto-rotate kicks in around the focused company until user interacts.
- ✅ **Replaced Radix Sheet with a plain div side panel** (`CompanySidePanel`) — Radix Sheet was firing `onOpenChange(false)` immediately after open on the WebGL canvas (interpreting canvas pointer events as outside-interact). The div panel avoids that whole class of bug and matches the Applicants City visual language. New testid: `job-detail-panel`.

### Bucket B — Backend hardening
- ✅ **In-memory sliding-window rate limiter** — `backend/services/rate_limit.py`. Per-(endpoint, identifier) deque of timestamps, with `Retry-After` header on 429.
- ✅ Wired into `/api/jobs/{job_id}/summary` (20 calls / 60s per IP+user, cache-miss path only) and `/api/jobs/{job_id}/match-score` (10 calls / 3600s per authenticated user, cache-miss path only)
- ✅ **Applicants-city limit** — `/api/applicants-city/buildings?limit=500` (default 500, max 2000). Mongo cursor now `.sort("applications_count", -1).limit(limit)` so the most active 500 towers always make the cut. Response includes `total` + `returned` for the frontend to surface a "showing top N of M" badge later.

### Bucket C — Profile completeness score
- ✅ **New `ProfileCompleteness` component** on `/profile` — SVG ring (red <60%, amber 60–99%, green ≥100%), centered percentage, 2-column checklist beneath
- ✅ 5-item rubric (each 20%): job title set, ≥3 skills, resume URL, GitHub linked, ≥1 application submitted
- ✅ testids: `profile-completeness`, `profile-completeness-ring`, `profile-completeness-pct`, `profile-check-{title|skills|resume|github|application}`
- ✅ Demo user shows 60% (skills + github + application done; title + resume todo) — verified visually

## Iteration 9 — Jun 20, 2026 (real ATS ingest + rich filters)

### Ingest pipeline (`backend/ingest/`)
- ✅ New module: `companies.py` (curated 71 company → ATS slug list), `locations.py` (alias-aware city parser → lat/lng), `extract.py` (regex tech/level/salary), `normalize.py` (shared `NormalizedJob` TypedDict + deterministic IDs), `runner.py` (parallel httpx fetch + Mongo upsert + stale-job expiry).
- ✅ **5 ATS adapters** (`adapters/{greenhouse,lever,ashby,workable,recruitee}.py`) — all public unauthenticated JSON endpoints, no API keys needed → safe for open source.
- ✅ **CLI**: `python -m ingest.cli verify` (pings every slug, reports 404s) and `python -m ingest.cli run [--source NAME]` (full or filtered ingest). Output writes a row to `db.ingest_runs` for observability.
- ✅ **Tech extraction**: 50+ canonical tags (Python, React, AWS, Kubernetes, LLMs, etc.) with word-boundary aware regex so "go" doesn't match "google". Verified on real data: top hits are Python (701), LLMs (666), SQL (571), ML (570), AWS (363), Kubernetes (262).
- ✅ **Level inference**: title-first regex (`Senior|Sr|Staff|Principal|Lead|Architect` → senior; `Intern|Jr|Junior|New Grad|Entry|Associate` → entry; else mid). Verified across 10 title shapes via unit tests.
- ✅ **Salary parsing**: `$120K - $180K` / `$145,000 to $210,000` / `120 - 180` → `(120000, 180000)`. Ashby's structured `compensation.compensationTiers[*].components[*]` parsed separately.
- ✅ **Location parsing**: 90+ city aliases (NYC, SF, Bay Area, Mountain View → San Jose cluster, Cambridge → Boston cluster). Remote-with-no-city falls back to company HQ so the city stays visible.
- ✅ **First production ingest**: 3831 real jobs from 39 companies across 28 US cities in 36s. Top cities: SF (2491 jobs), NYC (807), Seattle (126), Chicago (93). Top techs: Python, LLMs, SQL, ML, AWS, Kubernetes, TypeScript, GCP, Java, React.

### Scheduler
- ✅ **APScheduler `AsyncIOScheduler`** wired into FastAPI lifespan (`services/scheduler.py`). Runs initial ingest at boot+30s, then every 6h (overridable via env: `INGEST_INTERVAL_HOURS`, `INGEST_STARTUP_DELAY_S`, `INGEST_SCHEDULER_DISABLED=1`). Verified: scheduler executed initial run after backend restart, found 38 companies, updated 3627 jobs, expired 204 stale.
- ✅ Old `services/ingestion.py` (RemoteOK + small Greenhouse) left in place but unused — superseded by `ingest/runner.py`.

### `/api/jobs` filter expansion
- ✅ New filters on `GET /api/jobs`: `role` (title substring), `tech` (CSV OR-match against `skills`), `level` (entry/mid/senior), `posted_within` (e.g. `24h`, `7d`, `30d`, `1w`), `source` (ats name). All compose via AND.
- ✅ New endpoint **`GET /api/jobs/filters`** returns live facets: levels, sources, cities, top 40 tech tags with counts → frontend dropdowns can be data-driven.

### Seed migration
- ✅ **Removed all fake job/company seeding from `scripts/seed.py`** — only demo+admin users and 30 demo applicants are seeded now (they don't depend on real ATS data). Jobs + companies are ingested live.
- ✅ Dropped all existing seed jobs (763) and companies (39) from the DB before first real ingest.

### Tests
- ✅ `tests/test_ingest.py` — 29 unit tests covering extract (skills, level, salary, HTML sanitization, posted_at parsing) and locations (alias map + remote detection). Runs offline, sub-second.
- ✅ `tests/test_jobs_filters.py` — 7 integration tests against the live FastAPI app verifying every new filter actually narrows the result set correctly.
- ✅ All 15 pre-existing backend tests still pass (auth, security, applicants, jobs aggregation).

### Known deferred items
- 🟡 **3D building overflow** (SF/LA towers spilling past the West-Coast map edge) — deferred to next session per user. The spiral layout in `CompanyBuildings.jsx` needs a per-city radius cap or pyramid stacking when company count > ~12.
- 🟡 Recruitee + Workable adapters work but their slug coverage in the curated list is weak (most 404). Adding more EU companies for Recruitee/Personio later.

## Iteration 10 — Jun 21, 2026 (role categorization — software/robotics IC focus)

User saw manager/talent/PM roles in Jobs City and asked: "I'm getting manager roles, I'm targeting software, robotics roles."

### Classifier
- ✅ **New `backend/ingest/classify.py`** — 12-bucket regex classifier with deterministic load-bearing pattern order:
  1. **management** (Engineering Manager, Director, VP, Head of, CTO/CPO/COO etc.)
  2. **business** (sales, marketing, talent, HR, recruiting, finance, legal, risk, audit, brand, ops, etc.)
  3. **product** (PM, TPM, Program Manager, Product Marketing)
  4. **design** (Product Designer, UX, UI Designer)
  5. **robotics** (robotics, autonomy, SLAM, sensor fusion, controls, perception, mechatronics, manipulation, drone/UAV)
  6. **ml** (ML/AI Engineer, Applied Scientist, Research Scientist, CV, NLP, LLM, RL)
  7. **data** (Data Engineer, Analytics Engineer, BI, Data Scientist)
  8. **security** (Security Engineer/Architect/Analyst, AppSec, InfoSec, Red Team, Cryptography)
  9. **infra** (DevOps, SRE, Platform, Cloud, Reliability)
  10. **hardware** (Hardware/Electrical/Mechanical Engineer, ASIC, FPGA, Firmware, Embedded)
  11. **software** (generic SWE, Backend, Frontend, Full-Stack, Mobile, iOS, Android, Developer)
  12. **business (catch-all)** — final fallback for Manager/Lead/Director without engineering qualifier.
- ✅ **`TECHNICAL_IC`** frozenset = {software, robotics, ml, data, security, infra, hardware}. Default for the public `/api/jobs` listing + the 3D city.
- ✅ Adapters (all 5 ATSes) call `classify(title)` → `NormalizedJob.category` at ingest time. New backfill script `scripts/reclassify_jobs.py` reclassifies existing rows after edits without re-fetching.

### API contract
- ✅ **`GET /api/jobs?category=…`** — new query param:
  - omitted → defaults to TECHNICAL_IC (1336 jobs, was 3971 with everything)
  - `category=all` → no gating
  - `category=software,robotics` → CSV OR-match
  - **invalid input** (e.g. `?category=garbage`) → falls back to TECHNICAL_IC default (does NOT silently bypass — fixed via iter-7 RCA)
- ✅ Same param on **`GET /api/jobs-city/buildings`** so the 3D scene only shows tech roles.
- ✅ **`GET /api/jobs/filters`** now returns a `categories: [{name, count}, …]` field sorted desc by count.
- ✅ Shared helper `_build_category_filter()` in `routes/jobs.py` is the single source of truth for both endpoints — no drift possible.

### Robotics company seed
- ✅ Added 5 robotics companies to `ingest/companies.py`: Nuro, Wing (Greenhouse), 1X Technologies, Physical Intelligence, Figure (Ashby). Dropped 9 other robotics slugs that 404'd. Robotics role count went **4 → 22**.

### Live numbers
- Total ingested: **3971 active jobs from 42 companies, 28 US cities, 5 ATSes**
- Category breakdown: business 1854 (excluded), software 862, management 314 (excluded), product 296 (excluded), ml 190, data 136, other 108 (excluded), security 77, design 63 (excluded), infra 45, robotics 22, hardware 4.
- **Default city view: 1336 jobs across 12 cities** — managers, sales, recruiters, PMs filtered out.

### Tests
- ✅ `tests/test_classify.py` — 60+ assertions including boundary cases (`Engineering Manager` ≠ software, `Talent Operations - Program Manager` ≠ product, `ASIC Design Engineer` ≠ design, `Senior Manager, Market Management` = business).
- ✅ Testing agent iter-7 found 1 HIGH bug (invalid category bypassed filter) — fixed, re-tested in iter-8 with 11/11 green.


- `demo@jobcity.app` / `Demo123!` (applicant, 5 applications)
- `admin@jobcity.app` / `Admin123!` (admin)
- Stored in `/app/memory/test_credentials.md`

## Prioritized backlog

### P0 — Done (shipped)
- [x] Auth, seed, ingestion, jobs-city, applicants-city, apply, profile, compare, navbar

### P1 — Next features
- [x] ~~Search/filter bars wired into 3D cities~~ (Jobs City + Applicants City both done)
- [x] ~~Lever + YC/HN public ingestion sources~~
- [x] ~~Background scheduled ingestion via FastAPI~~ (6h)
- [x] ~~GitHub linking + commit count sync~~ (public API, no OAuth)
- [x] ~~InstancedMesh refactor for cities with > 500 buildings~~ (perf)
- [x] ~~Multi-tier skyscraper geometry for tall buildings~~ (both cities, ≥8 floors)
- [ ] LinkedIn / Indeed (no public APIs available — defer or scrape)
- [ ] Mobile-detection → simplified scene (no shadows, no Stars)
- [ ] Pagination/virtualization for applicants when count > 500
- [ ] Email verification + password reset
- [ ] Public share cards ("my JobCity building" PNG)

### P2 — Intelligence layer
- [x] ~~Claude Sonnet 4.5 job-match score~~ (24h cached)
- [ ] Resume upload (object storage) → parse → auto-fill profile + skills
- [ ] Recommended jobs panel (pre-compute match for top-10 jobs nightly)
- [ ] Weekly Top Hiring City leaderboard
- [ ] Achievement badges on top of buildings
- [ ] Recruiter persona with saved searches

## Known constraints
- Preview Cloudflare proxy overrides `Access-Control-Allow-Origin` to `*` with credentials; we rely on Bearer header for programmatic calls, cookies for browser session.
- visual-edits babel plugin injects `x-*` attributes on every JSX element in dev; node_modules patch is applied at `/app/frontend/scripts/patch-r3f.sh` (run after any `yarn install`).
 reset
- [ ] Public share cards ("my JobCity building" PNG)

### P2 — Intelligence layer
- [ ] Claude Sonnet 4.5 job-match score (Emergent LLM key)
- [ ] Resume upload (object storage) → parse → auto-fill profile + skills
- [ ] Recommended jobs panel
- [ ] Weekly Top Hiring City leaderboard
- [ ] Achievement badges on top of buildings
- [ ] Recruiter persona with saved searches

## Known constraints
- Preview Cloudflare proxy overrides `Access-Control-Allow-Origin` to `*` with credentials; we rely on Bearer header for programmatic calls, cookies for browser session.
- visual-edits babel plugin injects `x-*` attributes on every JSX element in dev; node_modules patch is applied at `/app/frontend/scripts/patch-r3f.sh` (run after any `yarn install`).
