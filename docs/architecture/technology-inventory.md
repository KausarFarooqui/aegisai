# AEGISAI — Technology & License Inventory

Per the MODUS requirement: every technology actually used, its real
version (from `requirements.txt`/`package.json`, not guessed), its
license, and a commercial-use note. Licenses below reflect the
well-established, standard license each project publishes — accurate to
general knowledge of these widely-used projects, but **verify against each
package's actual `LICENSE` file / PyPI / npm registry page before final
submission** if this needs to hold up to scrutiny; that's a five-minute
check MODUS explicitly asks for ("do not invent license information"),
not something to take on faith from any single source, including this one.

## Backend (Python)

| Technology | Version (pinned) | Purpose | License | Commercial use |
|---|---|---|---|---|
| FastAPI | 0.115.0 | Web framework, API layer | MIT | Unrestricted |
| Uvicorn | 0.32.0 | ASGI server | BSD-3-Clause | Unrestricted |
| Pydantic | 2.9.2 | Data validation, settings | MIT | Unrestricted |
| Pydantic Settings | 2.5.2 | Env-based config | MIT | Unrestricted |
| SQLAlchemy | 2.0.35 | ORM | MIT | Unrestricted |
| Alembic | 1.13.3 | DB migrations | MIT | Unrestricted |
| psycopg (v3) | 3.2.3 | PostgreSQL driver | LGPL-3.0 | Unrestricted as an unmodified dependency — LGPL's copyleft only applies if you modify and redistribute psycopg itself, which this project does not |
| pgvector (Python) | 0.3.5 | SQLAlchemy pgvector type | MIT | Unrestricted |
| Groq SDK | 0.11.0 | Groq API client | MIT | Unrestricted (SDK itself; the Groq *service* has its own free-tier terms — see below) |
| sentence-transformers | 3.2.0 | Local embedding model | Apache-2.0 | Unrestricted |
| NumPy | 1.26.4 | Numerical computing | BSD-3-Clause | Unrestricted |
| python-dotenv | 1.0.1 | `.env` loading | BSD-3-Clause | Unrestricted |
| Tenacity | 9.0.0 | Retry logic | Apache-2.0 | Unrestricted |
| httpx | 0.27.2 | HTTP client (Ollama calls) | BSD-3-Clause | Unrestricted |
| pytest | 8.3.3 | Test framework | MIT | Unrestricted |
| pytest-asyncio | 0.24.0 | Async test support | Apache-2.0 | Unrestricted |

## Database & AI infrastructure

| Technology | Version | Purpose | License | Commercial use |
|---|---|---|---|---|
| PostgreSQL | 16 (17 on Supabase) | Primary datastore | PostgreSQL License (permissive, MIT/BSD-like) | Unrestricted |
| pgvector | 0.6.0 (local) | Vector similarity search | PostgreSQL License | Unrestricted |
| Supabase | free tier | Managed Postgres hosting | Proprietary platform; free tier, no card required | Free tier sufficient for this project's scale — see decision log for what changes at 10,000+ processes |
| Groq API | free tier | Primary LLM provider (Llama 3.3 70B) | Proprietary service; free tier, no card required | Free tier used throughout — see decision log for rate-limit notes and the fallback design |
| Ollama | local | Fallback LLM runtime | MIT (Ollama itself) | The specific model run locally (e.g., Llama 3.2) carries its own separate license from its publisher (Meta's Llama license) — free for this use case; review Meta's license directly if ever deploying at a scale their terms specifically restrict |
| sentence-transformers model (all-MiniLM-L6-v2) | — | Local embeddings | Apache-2.0 | Unrestricted |

## Frontend (Node/npm)

| Technology | Version | Purpose | License | Commercial use |
|---|---|---|---|---|
| React / React DOM | 19.2.8 | UI framework | MIT | Unrestricted |
| TypeScript | 6.0.2 | Type checking | Apache-2.0 | Unrestricted |
| Vite | 8.2.0 | Build tool / dev server | MIT | Unrestricted |
| Tailwind CSS | 4.3.3 | Styling | MIT | Unrestricted |
| react-router-dom | 7.18.2 | Client-side routing | MIT | Unrestricted |
| @tanstack/react-query | 5.101.4 | Server-state management | MIT | Unrestricted |
| reactflow | 11.11.4 | 2D graph visualization | MIT | Unrestricted |
| react-force-graph-3d | 1.29.1 | 3D graph visualization | MIT | Unrestricted |
| three.js | 0.185.1 | WebGL rendering (underlies the 3D graph) | MIT | Unrestricted |
| recharts | 3.10.1 | Dashboard charts | MIT | Unrestricted |
| lucide-react | 1.31.0 | Icons | ISC | Unrestricted |
| clsx | 2.1.1 | Conditional class names | MIT | Unrestricted |

## Summary

**Every technology in this stack is free to run and demonstrate — no paid
license is required at any point**, satisfying the MODUS free-technology
requirement directly:
- All open-source libraries are permissively licensed (MIT/BSD/Apache-2.0),
  with the one LGPL exception (`psycopg`) posing no restriction for this
  project's usage pattern (unmodified dependency, not redistributed).
- The two external services used (Supabase, Groq) both have genuinely free
  tiers with no credit card requirement, and both have a documented
  fallback/migration story if that ever changed (local Postgres for
  Supabase; Ollama for Groq — see decision log).
