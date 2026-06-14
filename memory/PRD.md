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

## What's been implemented (Feb 14, 2026)
- ✅ JWT email/password auth + Emergent Google session bridge
- ✅ MongoDB models with UUID `user_id` (no ObjectId leakage), unique indexes
- ✅ Seed script: 20 companies, ~351 templated jobs, 30 demo applicants, 204 demo applications, admin + demo accounts
- ✅ Real data ingestion: RemoteOK (19 jobs) + Greenhouse (756 jobs from Stripe, Airbnb, Anthropic, Databricks, Vercel)
- ✅ Aggregation endpoints: `/api/jobs-city/buildings` and `/api/applicants-city/buildings`
- ✅ 3D Jobs City — extruded USA polygon, company buildings clustered per city with spiral layout, dusk lighting, city label rings
- ✅ 3D Applicants City — cyan grid floor, voxel towers colored by experience level (blue/amber/red), GitHub antennas, night palette
- ✅ Apply flow with duplicate prevention, cover note, toast feedback
- ✅ Profile page with my-building link + applications list
- ✅ Compare page with bar charts and top-companies stats
- ✅ Landing page with dual-image hero, glass-morphism, Unbounded + Outfit + JetBrains Mono fonts
- ✅ NavBar with sign-in/out/profile links
- ✅ r3f patched to ignore `x-*` JSX props injected by visual-edits babel plugin
- ✅ Testing agent run: 14/14 backend pytest + Playwright e2e all green

## Test credentials
- `demo@jobcity.app` / `Demo123!` (applicant, 5 applications)
- `admin@jobcity.app` / `Admin123!` (admin)
- Stored in `/app/memory/test_credentials.md`

## Prioritized backlog

### P0 — Done (shipped)
- [x] Auth, seed, ingestion, jobs-city, applicants-city, apply, profile, compare, navbar

### P1 — Next features
- [ ] Search/filter bars wired into 3D cities (search input already exists in Jobs City UI — filter buildings/highlight on match)
- [ ] LinkedIn/Indeed/YC public ingestion sources
- [ ] GitHub OAuth linking + automatic commit count sync
- [ ] InstancedMesh refactor for cities with > 500 buildings (perf)
- [ ] Mobile-detection → simplified scene (no shadows, no Stars)
- [ ] Pagination/virtualization for applicants when count > 500
- [ ] Background scheduled ingestion via FastAPI BackgroundTasks (refresh every 6h)
- [ ] Email verification + password reset
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
