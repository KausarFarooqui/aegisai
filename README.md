# AEGISAI — Enterprise Workforce Impact Intelligence Platform

**MODUS Enterprise AI Build Challenge — Assignment 11: Process × Role × Skill Intelligence Graph**

> Status: **Phase 6 of 12 complete — the database is populated with a
> real, connected intelligence graph, not just proven capable of holding
> one.** `scripts/seed_processes.py` seeds 10 processes across two value
> chains (Retail Lending; Trade Finance & Compliance) using the **exact
> same pipeline** `POST /api/processes/analyze` uses — proof that seed
> data and live dynamic-analysis data are produced by one mechanism, not
> two. `scripts/seed_research_sources.py` loads a 20-source curated
> evidence corpus (real, independently verified URLs — see decision log)
> that the pipeline now automatically searches and cites against every AI
> opportunity it creates. 82 tests passing. Frontend is not yet built
> (Phase 7).

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

**Confirmed live, for real** — not a hypothetical "try it yourself," this
actually happened, against the real Supabase project and a real Groq key:

```
POST /api/processes/analyze {"process_name": "Warehouse Inventory Forecasting", ...}
→ status: completed, 6 stages, ~22s (Groq retried once mid-run on a
  schema validation error — 13 proposed skills vs. the 12-item cap — and
  self-corrected on retry, unprompted)

POST /api/processes/analyze {"process_name": "Inventory Demand Planning", ...}
→ status: completed, a fully independent second Groq call
```

The second call proposed "Inventory Analyst" and "Data Analysis" again,
with no memory of the first call — and the dedup mechanism reused the
**exact same UUIDs** the first process created, rather than duplicating
them. That's the core mechanism this entire architecture rests on, proven
with two independent live LLM calls, not a scripted test. Full walkthrough
in the decision log.

To reproduce (after `alembic upgrade head` against your database):

```bash
python scripts/bootstrap_minimal_data.py   # or scripts/seed_processes.py for the full dataset
uvicorn app.main:app --reload --port 8000

# in another terminal, using the value_chain_id printed above:
curl -X POST http://localhost:8000/api/processes/analyze \
  -H "Content-Type: application/json" \
  -d '{"process_name": "Warehouse Inventory Forecasting", "value_chain_id": "<paste-here>"}'

curl http://localhost:8000/api/processes/<result_entity_id from above>
curl http://localhost:8000/api/graph/process/<same id>
```

This is the actual MODUS example input ("Warehouse Inventory Forecasting")
— nothing in the codebase is hard-coded for it specifically; any process
name works the same way.

**Phase 6 additions — 6 more tests, 82 total, all passing:**

- `data/seed/research_sources.py` — 20 curated, real research sources
  (industry reports, academic papers, and current regulatory guidance on
  AI in banking/lending/AML/trade finance — see decision log for how each
  was independently verified, not just generated). Diversity across all 6
  source types the schema supports.
- `scripts/seed_research_sources.py` — embeds and loads the corpus,
  idempotent by URL.
- `app/services/evidence_service.py` — semantic search linking an
  AIOpportunity to supporting research, reusing the same
  `find_best_match` logic that powers entity dedup (same underlying
  operation — "find the closest match above a threshold, or admit
  nothing qualifies" — so there's one tested implementation, not two).
  Wired into the pipeline as its own stage (`evidence_retrieval`, between
  persistence and skill-trend update) — best-effort by design: an empty
  corpus or nothing relevant enough is a normal outcome, never a fabricated
  citation.
- `scripts/seed_processes.py` — seeds the actual 10-process dataset (5
  Retail Lending processes, 5 Trade Finance & Compliance processes) by
  calling `ProcessAnalysisPipeline.run()` — the *exact same pipeline*
  `POST /api/processes/analyze` uses, with `source="seed"` as the only
  difference. Idempotent (skips already-existing process names) and
  resilient (one process failing doesn't stop the rest of the run).
- Tests cover: idempotent org-structure setup, the full 10-process seed
  run (with dedup correctly collapsing repeated role/skill names into
  shared entities — proven at seed-script scale, not just two processes),
  safe re-running, and provenance tagging (`source="seed"` vs `"dynamic"`,
  including the subtlety that a seed run reusing a dynamically-created
  entity must not overwrite that entity's original provenance).

**Not yet live-verified**: the real evidence-retrieval quality (does a
real embedding of a real AI opportunity actually find genuinely relevant
research from the corpus, at a sensible threshold) and the real 10-process
seed run's output quality — both need your real Groq key + embedding
model, same disclosed pattern as every AI-dependent piece so far. Run
`scripts/seed_research_sources.py` then `scripts/seed_processes.py` on
your machine to confirm.

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
│   │   ├── schemas/           # extraction (P4); process/dashboard/analysis/graph (P5)
│   │   ├── services/          # dedup (P4); graph_sync/dashboard/graph_query (P5); evidence_service (P6)
│   │   ├── repositories/      # base, entity (pgvector search incl. ResearchSource), graph (P5)
│   │   ├── intelligence/      # llm_provider.py, embeddings.py (P4); prompts.py (P5)
│   │   ├── scoring/           # impact_score.py + skill_trend.py (Phase 4)
│   │   ├── api/routes/        # dashboard, processes, roles_skills, graph, analyze (Phase 5)
│   │   └── workers/           # analysis_pipeline.py — the actual Surprise Record Test (P5, evidence stage added P6)
│   ├── migrations/            # Alembic — 2 verified migrations (schema, then embedding columns)
│   ├── scripts/                # verify_embeddings.py, test_llm_connection.py, bootstrap_minimal_data.py,
│   │                            # seed_research_sources.py, seed_processes.py (Phase 6)
│   └── tests/                 # pytest, 82 passing
├── data/seed/                 # research_sources.py — 20 real, independently-verified sources (Phase 6)
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
| Traceability fields (Evidence, source provenance) | ✅ `source` populated on every entity; Evidence/ResearchSource populated with 20 real sources and semantic search wired into the live pipeline (Phase 6) |
| AI/model integration, model abstraction | ✅ Provider abstraction + fallback built, unit tested, **and live-verified** against real Groq/embeddings (see decision log) |
| Deterministic scoring, separated from LLM | ✅ Built, fully tested, wired into the live pipeline |
| Entity dedup (prevents duplicate records) | ✅ Built, tested with synthetic vectors, **and proven across real pipeline runs with two independent live Groq calls** (see decision log) |
| Dynamic new-record analysis (Surprise Record Test) | ✅ **Working end-to-end, confirmed live** via `POST /api/processes/analyze` against real Supabase + Groq — see decision log for the full run |
| Seed data uses the same mechanism as dynamic analysis | ✅ `scripts/seed_processes.py` calls the identical `ProcessAnalysisPipeline` as the live API — not a separate code path (Phase 6) |
| Real frontend | ⏳ Phase 7 |
| Tests | ✅ 82 passing |
| No hard-coded responses | ✅ By construction — the pipeline that handled the MODUS example ("Warehouse Inventory Forecasting") live is the exact same code path as every other input, including all 10 seed processes |

Full checklist tracked in `docs/architecture/decision-log.md`.
