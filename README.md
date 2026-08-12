# AEGISAI — Enterprise Workforce Impact Intelligence Platform

**MODUS Enterprise AI Build Challenge — Assignment 11: Process × Role × Skill Intelligence Graph**

> Status: **Phase 5 of 12 complete — the Surprise Record Test actually
> works, end to end, through the real HTTP API.** `POST /api/processes/
> analyze` runs the full pipeline (validate → LLM extraction → embedding
> dedup → deterministic scoring → transactional persistence → skill-trend
> recompute → graph sync) and is provably correct — 68 tests passing,
> including full pipeline runs against a real Postgres database and a
> proof that re-analyzing with overlapping role/skill names reuses
> existing entities instead of duplicating them. What's *not* yet
> live-verified is the real Groq call and real embedding model inside
> this exact endpoint (same disclosed gap as Phase 4 — see below).
> Frontend is not yet built (Phase 6).

## What this is

Northstar Bank is a fictional retail bank. AEGISAI models its value chain,
processes, activities, roles, and skills as a connected graph, then overlays
AI opportunities and their impact so the app can answer questions like
*"if AI automates this activity, what roles and skills does that cascade
into?"* — including for a process/role/skill nobody seeded, entered live.

Full requirements, architecture, and rationale are in
[`docs/architecture/decision-log.md`](docs/architecture/decision-log.md).

## Why Assignment 11, why this stack

Covered in depth in the architecture doc. Short version: Assignment 11 is
the one MODUS assignment whose own demo script ("select a process → see
roles → select a role → see skills...") is identical to its own
requirements, and it structurally covers Assignments 4, 5, and 6 as views
of one graph rather than three separate builds.

## Tech stack

| Layer | Choice | Cost |
|---|---|---|
| DB | PostgreSQL 16 + pgvector (Supabase free tier) | Free |
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2 | Free/OSS |
| LLM (primary) | Groq (Llama 3.3 70B), free tier | Free |
| LLM (fallback) | Ollama, local model | Free/local |
| Embeddings | sentence-transformers (local, no external dependency) | Free |
| Frontend | React + TypeScript + Tailwind + React Flow + Recharts | Free/OSS |

No paid license is required to run or demo this application, per the
MODUS free-technology requirement.

## What's actually verified (Phase 3)

Every claim below was run, not assumed:

- All 19 tables (13 entities + 6 junction/graph tables) build cleanly from
  SQLAlchemy metadata with zero relationship errors
- A real Alembic migration was generated and applied against a live
  PostgreSQL 16 + pgvector 0.6.0 instance
- Full `downgrade → upgrade` round-trip confirmed clean (this caught a real
  bug — see `docs/architecture/decision-log.md` § "Issues found during
  verification")
- A connected slice of the actual domain graph (Industry → ValueChain →
  Process → Activity → Role → Skill, plus an AIOpportunity with a scored
  AIAssessment) was written and read back through the ORM relationships —
  not raw SQL — proving `back_populates`/`secondary=` wiring is correct
- The FastAPI app boots and `/api/health` reports a live DB connection
- `pytest` suite (3 tests: hierarchy round-trip, scoring formula, enum
  value regression) passes against a live database

**Phase 4 additions — 42 more tests, 45 total, all passing:**

- `app/scoring/impact_score.py` — the weighted AI Impact Score formula and
  band classification (LOW/MEDIUM/HIGH/VERY_HIGH), pure function, all 9
  boundary cases tested exactly (e.g. 30.99 → LOW, 31 → MEDIUM)
- `app/scoring/skill_trend.py` — deterministic skill-trend classification
  (Emerging/Increasing/AI-Augmented/Declining/Enduring/Changing) from
  linked AI opportunities, fully tested including the mixed-signal case
- `app/services/dedup_service.py` — the embedding-similarity entity
  matching that prevents duplicate roles/skills across dynamic analysis
  runs, tested with synthetic vectors covering near-duplicate detection,
  genuinely-different rejection, multi-candidate ranking, and configurable
  thresholds
- `app/intelligence/llm_provider.py` — the Groq/Ollama provider
  abstraction's fallback and retry-with-validation control flow, tested
  with fake providers (network-independent)
- `app/schemas/extraction.py` — the Pydantic contract the LLM's output
  must satisfy, tested directly

**Two pieces needed one-command verification on your machine — both now
confirmed live**, against the real Supabase project and a real Groq key
(not simulated): Groq responds and validates correctly; Ollama's fallback
path was exercised via a clean "not running" skip rather than a crash;
real embeddings separate near-duplicate role/skill names (~0.90 cosine
similarity) from unrelated ones (~0.35) with the configured 0.86 threshold
sitting safely in between. Full numbers and the two real infrastructure
issues this surfaced (Supabase's IPv6-only direct connection on free tier,
and a stale local Postgres port) are in `docs/architecture/decision-log.md`.

**Phase 5 additions — 23 more tests, 68 total, all passing:**

- `app/workers/analysis_pipeline.py` — the actual Surprise Record Test
  implementation. 8 end-to-end tests running the real pipeline against a
  real Postgres database (not mocked), including the load-bearing proof:
  running it twice with overlapping role/skill names reuses the existing
  entities rather than duplicating them, verified by counting rows and by
  checking graph edges connect both processes to the same shared role.
  Also verified: clean failure (no partial writes) on a duplicate process
  name, a nonexistent value chain, malformed LLM output, and an LLM
  response with a dangling cross-reference.
- `app/api/routes/` — the full REST API (`/api/dashboard`, `/api/processes`,
  `/api/processes/{id}`, `/api/processes/analyze`, `/api/analysis/{id}`,
  `/api/roles`, `/api/skills`, `/api/graph/{node_type}/{id}`). 11 tests
  using FastAPI's TestClient with dependency-injected fake providers,
  covering the full round trip: analyze → fetch process detail → fetch
  the graph neighborhood, plus the "failed pipeline returns 200 with
  status=failed, not a 500" design (see decision log).
- Also live-verified by actually running the server (not just tests):
  booted `uvicorn` for real, hit `/api/health` and `/api/dashboard` with
  `curl` against the real local Postgres — this is what caught a genuine
  Alembic gotcha (`Base.metadata.drop_all()` doesn't touch the
  `alembic_version` table, since Alembic manages it outside
  `Base.metadata` — so a naive "tests dropped everything, then re-run
  `alembic upgrade head`" silently does nothing). Full account in the
  decision log.

**Try the real Surprise Record Test yourself** (after `alembic upgrade
head` against your database):

```bash
python scripts/bootstrap_minimal_data.py   # creates one Industry/Org/ValueChain
uvicorn app.main:app --reload --port 8000

# in another terminal, using the value_chain_id the bootstrap script printed:
curl -X POST http://localhost:8000/api/processes/analyze \
  -H "Content-Type: application/json" \
  -d '{"process_name": "Warehouse Inventory Forecasting", "value_chain_id": "<paste-here>"}'

# then fetch the result:
curl http://localhost:8000/api/processes/<result_entity_id from above>
curl http://localhost:8000/api/graph/process/<same id>
```

This is the actual MODUS example input ("Warehouse Inventory Forecasting")
— nothing in the codebase is hard-coded for it specifically; any process
name works the same way.

## Setup (verified path — WSL2/Ubuntu)

```bash
# 1. Clone and enter the repo
git clone <your-github-repo-url> aegisai
cd aegisai/backend

# 2. Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Database — Supabase free tier (recommended, avoids local Postgres/disk issues)
#    Create a project at supabase.com, enable the "vector" extension in the
#    SQL editor (CREATE EXTENSION IF NOT EXISTS vector;), then copy the
#    connection string.
cp ../.env.example .env
# edit .env: set DATABASE_URL to your Supabase connection string,
# and GROQ_API_KEY from console.groq.com/keys (free, no card)

# 4. Apply the schema
alembic upgrade head

# 5. Run the tests (point DATABASE_URL at a disposable test DB first if you
#    don't want test data touching your dev DB)
pytest tests/ -v

# 6. Run the API
uvicorn app.main:app --reload --port 8000
# visit http://localhost:8000/api/health and http://localhost:8000/docs
```

### Alternative: local Postgres instead of Supabase

```bash
sudo apt-get install -y postgresql postgresql-contrib postgresql-16-pgvector
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'yourpassword';"
sudo -u postgres psql -c "CREATE DATABASE aegisai;"
sudo -u postgres psql -d aegisai -c "CREATE EXTENSION IF NOT EXISTS vector;"
# then set DATABASE_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/aegisai
```

Note: this path was hit exactly once during development after Supabase was
chosen as the primary target, purely to verify the schema locally — see the
decision log for why Supabase is still the recommended path for you day-to-day
(avoids the disk-space issue from the BioVision AI project's Docker deploy).

## Project structure

```
aegisai/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entrypoint — wiring only, no business logic
│   │   ├── config/settings.py # all env-driven config, one place
│   │   ├── models/            # SQLAlchemy models — the domain graph (Phase 3)
│   │   ├── db/session.py      # engine + session factory
│   │   ├── schemas/           # Pydantic schemas — extraction (P4), process/dashboard/analysis/graph (P5)
│   │   ├── services/          # dedup (P4); graph_sync, dashboard, graph_query (P5)
│   │   ├── repositories/      # base, entity (pgvector search), graph — all done (Phase 5)
│   │   ├── intelligence/      # llm_provider.py, embeddings.py (P4); prompts.py (P5)
│   │   ├── scoring/           # impact_score.py + skill_trend.py (Phase 4)
│   │   ├── api/routes/        # dashboard, processes, roles_skills, graph, analyze (Phase 5)
│   │   └── workers/           # analysis_pipeline.py — the actual Surprise Record Test (Phase 5)
│   ├── migrations/            # Alembic — 2 verified migrations (schema, then embedding columns)
│   ├── scripts/                # verify_embeddings.py, test_llm_connection.py, bootstrap_minimal_data.py
│   └── tests/                 # pytest, 68 passing
├── data/seed/                 # full seed data script + curated evidence corpus (Phase 6)
├── docs/
│   └── architecture/decision-log.md   # every architectural decision + why
├── frontend/                  # React app (Phase 7)
└── .env.example                # template — real .env is gitignored
```

## Status against the MODUS checklist so far

| Requirement | Status |
|---|---|
| Real backend, persistent DB | ✅ Built and verified live |
| Structured, normalized data model | ✅ 19 tables, typed FKs, verified |
| Traceability fields (Evidence, source provenance) | ✅ Modeled; `source` populated on every entity; Evidence/ResearchSource population is Phase 6 |
| AI/model integration, model abstraction | ✅ Provider abstraction + fallback built, unit tested, **and live-verified** against real Groq/embeddings (see decision log) |
| Deterministic scoring, separated from LLM | ✅ Built, fully tested, wired into the live pipeline |
| Entity dedup (prevents duplicate records) | ✅ Built, tested with synthetic vectors, **and proven across real pipeline runs** (see Phase 5 dedup test) |
| Dynamic new-record analysis (Surprise Record Test) | ✅ **Working end-to-end via `POST /api/processes/analyze`** — validated, tested, one gap: live Groq/embedding calls inside this exact endpoint need your credentials (same as Phase 4; try it with `scripts/bootstrap_minimal_data.py`) |
| Real frontend | ⏳ Phase 7 |
| Tests | ✅ 68 passing |
| No hard-coded responses | ✅ By construction — the pipeline that handles the MODUS example ("Warehouse Inventory Forecasting") is the exact same code path as every other input |
| Real frontend | ⏳ Phase 6 |
| Tests | ✅ 45 passing |
| No hard-coded responses | ✅ By construction — every "decision" (score, trend, match) is a tested function of its inputs, nothing is a fixed string |

Full checklist tracked in `docs/architecture/decision-log.md`.
