# AEGISAI — Enterprise Workforce Impact Intelligence Platform

**MODUS Enterprise AI Build Challenge — Assignment 11: Process × Role × Skill Intelligence Graph**

> Status: **Phase 3 of 12 complete.** Domain model, migrations, and DB
> connectivity are built and verified against a real PostgreSQL + pgvector
> instance (see "What's actually verified" below — this is not a claim,
> it's a log of what was run). API layer, AI pipeline, and frontend are not
> yet built. This README will be extended as each phase lands.

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
│   │   ├── models/            # SQLAlchemy models — the domain graph (Phase 3, done)
│   │   ├── db/session.py      # engine + session factory
│   │   ├── schemas/           # Pydantic request/response schemas (Phase 5)
│   │   ├── services/          # business rules — dedup, validation (Phase 4-5)
│   │   ├── repositories/      # all DB access goes through here (Phase 5)
│   │   ├── intelligence/      # LLM orchestration (Phase 4)
│   │   ├── scoring/           # deterministic AI-impact formula (Phase 4)
│   │   ├── graph/             # graph-edge assembly for React Flow (Phase 5)
│   │   └── workers/           # async analysis job runner (Phase 4)
│   ├── migrations/            # Alembic — one verified initial migration
│   └── tests/                 # pytest, run against a real Postgres DB
├── data/seed/                 # seed data script + curated evidence corpus (Phase 3b)
├── docs/
│   └── architecture/decision-log.md   # every architectural decision + why
├── frontend/                  # React app (Phase 6)
└── .env.example                # template — real .env is gitignored
```

## Status against the MODUS checklist so far

| Requirement | Status |
|---|---|
| Real backend, persistent DB | ✅ Built and verified live |
| Structured, normalized data model | ✅ 19 tables, typed FKs, verified |
| Traceability fields (Evidence, source provenance) | ✅ Modeled, not yet populated |
| AI/model integration | ⏳ Phase 4 |
| Dynamic new-record analysis (Surprise Record Test) | ⏳ Phase 4 |
| Real frontend | ⏳ Phase 6 |
| Tests | ✅ 3 passing, more added per phase |
| No hard-coded responses | N/A yet — nothing generates responses yet |

Full checklist tracked in `docs/architecture/decision-log.md`.
