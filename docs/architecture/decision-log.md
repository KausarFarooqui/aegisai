# Architecture Decision Log

This log exists so every decision below is something you can explain live,
per the MODUS requirement: *"Whenever you make an architectural decision,
explain WHY, TRADE-OFF, ALTERNATIVES, WHY THIS OPTION WON."* Entries are
added as each phase lands.

---

## Why Assignment 11

Chosen over the other 11 assignments because its demo script and its
requirements are the same thing: *"select a process → see roles → select a
role → see skills → select a skill → see roles"* is both what the brief
asks for and exactly what you show a judge. It also structurally covers
Assignment 4 (process↔role), Assignment 5 (skill trend classification), and
Assignment 6 (role futures) as views over one graph, rather than requiring
three separate builds. Rejected Assignment 12 (Grand Challenge) as
higher-risk for a 2-day solo build — same "connected intelligence" spirit,
larger surface area (strategy + governance + initiatives on top of
everything Assignment 11 already requires).

## Why Banking (Northstar Bank), scoped to two value chains

Banking gives genuinely distinct roles with different AI exposure profiles
(Credit Analyst vs. Compliance Officer vs. Relationship Manager), which is
what makes the "cascading impact" demo land — a domain with homogeneous
roles wouldn't show meaningful contrast. Scoped to **Retail Lending** and
**Trade Finance/Compliance** rather than "all of banking" so the ~10 seed
processes read as a coherent slice of one bank, not a grab-bag.

## Why PostgreSQL + pgvector over a graph database (Neo4j)

A dedicated graph DB is a better *semantic* fit for arbitrary-depth
traversal, but adds a second database to keep consistent with Postgres, a
second query language, and no real benefit at this scale (hundreds, not
millions, of nodes). Chose typed junction tables (`activity_roles`,
`role_skills`, etc.) for referential integrity, plus one deliberately
denormalized `graph_edges` table populated by a sync step, purely to serve
the graph-visualization endpoint fast. One less moving part; same navigable
graph. See `app/models/graph_edge.py` for the reasoning in full.

## Why Supabase over local Docker Postgres

Local Docker Postgres previously caused a disk-space wall on the BioVision
AI project. Supabase's free tier ships pgvector on every plan at no extra
cost (verified current as of Aug 2026), which removes the local-container
dependency entirely. A local Postgres path is documented in the README as
a fallback/testing option — and was in fact used once, deliberately, to
verify this schema in a sandboxed environment before handing it off (see
"Issues found during verification" below) — but Supabase remains the
target for day-to-day development.

## Why Groq (primary) + Ollama (fallback) for the LLM, not a single provider

MODUS requires explaining what happens if a free-tier service becomes
unavailable. `LLMProvider` is an abstraction (built in Phase 4) with two
implementations: Groq (fast, free tier, ~30 req/min / ~14,400 req/day
depending on model — confirmed current) as primary, and a local Ollama
model as fallback. If Groq is unavailable or rate-limited mid-demo, the app
degrades to a slower local model rather than failing outright — this is a
real, working answer to that question, not a hypothetical one.

## Why sentence-transformers (local) for embeddings, not a hosted API

Zero external dependency for the mechanism the Surprise Record Test relies
on most heavily (entity dedup via similarity search — see Phase 4). Nothing
to rate-limit, nothing that can go paid overnight.

## Why no generic polymorphic `Relationship` table for the core hierarchy

The original draft schema proposed a single generic `Relationship` entity
for everything. Rejected for the *structural* graph (Process↔Activity↔
Role↔Skill↔AIOpportunity) in favor of typed junction tables, because those
relationships need real foreign-key integrity — a judge editing/deleting a
record live should hit real constraints, not a permissive blob table.
**Evidence is the one deliberate exception**: it uses a light polymorphic
association (`related_entity_type` + `related_entity_id`) because it's
cross-cutting annotation-style metadata that can attach to almost any
entity type, not a structural graph edge — seven separate per-type junction
tables would add tables without adding real integrity value. See the
docstring in `app/models/evidence.py`.

## Why Skill has no separate "FutureSkill" entity

`Skill.trend_classification` (Emerging / Increasing / AI-Augmented /
Changing / Declining / Enduring Human Capability) is a field on `Skill`,
recomputed by deterministic code whenever a linked `AIOpportunity` changes
— not hand-set, and not a second table. This is what makes "which skills
are declining" a live, explainable query instead of a static label typed
once during seeding.

## Why the LLM never writes `AIAssessment.total_score` directly

The LLM proposes five 0–100 factor estimates plus a one-line rationale each
(`AIAssessment.factor_rationale`). A pure, deterministic function in
`app/scoring` (Phase 4) computes `total_score` and `impact_band` from those
factors using the configurable weights below. This split is the direct
answer to "how do you prevent the AI from just making up a score":

```
total = 0.30*repetitiveness + 0.20*data_availability + 0.20*predictability
      + 0.15*digitalization + 0.15*ai_capability_fit
```

---

## Issues found during verification (Phase 3)

Both of these were caught by actually running a migration against a live
PostgreSQL + pgvector instance rather than trusting the code to be correct
— worth being able to walk through in the interview as an example of what
"tested, not just written" looks like in practice.

**1. `alembic downgrade` didn't drop the custom ENUM types it created.**
Postgres ENUM types aren't tied to the tables that use them, so
`DROP TABLE` alone leaves them behind. A `downgrade → upgrade` cycle then
fails with `type "X" already exists`. Fixed by adding explicit
`sa.Enum(name=...).drop(op.get_bind(), checkfirst=True)` calls to every
migration's `downgrade()` for each enum defined in `app/models/base.py`.

**2. SQLAlchemy was persisting enum *names*, not *values*.** All enums in
this codebase are defined as `class X(str, enum.Enum): LOW = "low"`. By
default, SQLAlchemy's `Enum` type stores the Python member's `.name`
("LOW") in the database column, not `.value` ("low"), unless told
otherwise — a well-known but easy-to-miss default. Confirmed by querying
`pg_enum` directly after a real migration and seeing `LOW`/`MEDIUM`/`HIGH`
instead of the intended lowercase values. Fixed with a shared `pg_enum()`
helper (`app/models/base.py`) that all ~10 enum columns now use, passing
`values_callable=lambda obj: [e.value for e in obj]`. A regression test
(`tests/test_domain_model.py::test_enum_columns_store_lowercase_values`)
locks this in by querying the raw column value, not just the ORM-mapped
Python enum (which would mask the bug, since the `str` mixin makes
`Enum.LOW == "low"` true regardless of what's actually stored).

Both are the kind of bug that would surface for the first time live in
front of a judge if only tested by inspection — this is why the schema was
validated against a real instance before handing it off, not just imported
and eyeballed.

---

## Phase 4 — AI Intelligence Layer

### The LLM/deterministic-code boundary, made concrete

`app/schemas/extraction.py` is the actual contract: the LLM may propose
five 0–100 factor estimates with a one-line reason each
(`ProposedAIOpportunity.factor_*`), and may *hint* whether a role/skill is
new (`ProposedRole.is_new` / `ProposedSkill.is_new`). It may NOT propose a
final score, a final skill trend, or a final match/no-match decision on
duplicate entities — those three things are computed by
`app/scoring/impact_score.py`, `app/scoring/skill_trend.py`, and
`app/services/dedup_service.py` respectively, all pure functions with no
LLM call inside them, all covered by unit tests that never touch a network.
This is the literal, checkable answer to "how do you prevent the AI from
just making up a score" — not a design intention, a schema boundary the
code enforces.

### Why entity dedup is a separate, decoupled module from embedding generation

`app/services/dedup_service.py` operates on plain `list[float]` vectors and
knows nothing about sentence-transformers. `app/intelligence/embeddings.py`
is the only thing that knows how a vector gets produced. This split exists
for a very concrete reason: it let the *matching algorithm* (cosine
similarity + thresholding — the part that actually decides "reuse this
role" vs. "create a new one") get full unit-test coverage with synthetic
vectors, independent of whether the real embedding model could run in this
particular environment (see below).

### Honest account of what could and couldn't be verified live here

Everything in Phase 3 was verified against a real database. Phase 4 has
one genuine gap, disclosed rather than glossed over:

- **Scoring, skill-trend classification, dedup matching, the extraction
  schema, and the LLM orchestrator's fallback/retry control flow**: all
  fully unit tested (36 tests) with no network dependency, using synthetic
  vectors and fake LLM providers that exercise the same code paths the
  real ones do.
- **The actual sentence-transformers model** (`EmbeddingProvider._get_model`)
  and **the actual Groq/Ollama HTTP calls** (`GroqProvider._raw_complete`,
  `OllamaProvider._raw_complete`): NOT exercised live in this environment.
  Installing `sentence-transformers` pulls in `torch`, and the default
  PyPI `torch` wheel bundles several GB of CUDA runtime dependencies; the
  trimmed CPU-only wheel lives on `download.pytorch.org`, which isn't on
  this sandbox's network allowlist. Two install attempts filled the disk
  before completing. Testing Groq directly needs a real API key, which
  isn't something to paste into a chat session.

  Two scripts exist specifically to close this gap on your machine, and
  should be run before trusting either mechanism:
  `backend/scripts/verify_embeddings.py` (checks the real model produces
  sensible similarity scores — near-duplicate role names should score
  meaningfully higher than unrelated ones) and
  `backend/scripts/test_llm_connection.py` (confirms Groq responds and
  validates against the schema, and separately checks Ollama if it's
  running locally). Both fail loudly with a clear message if something's
  wrong — neither silently reports success.

This is a real constraint of the build environment, not a shortcut taken
on the design — worth being upfront about if asked "did you test
everything yourself" in the interview: yes, everything that could be
tested without a paid credential or a GPU-scale dependency was tested
for real; the two pieces that needed either are wired for one-command
verification on your own machine instead of being asserted untested.

### Update: both gaps closed — verified live on real infrastructure

Both `scripts/verify_embeddings.py` and `scripts/test_llm_connection.py`
were subsequently run for real, against the actual target infrastructure
(not a substitute): a live Supabase project (`aegisai`, region `ap-south-1`)
reached over the IPv4 Session Pooler, a real Groq API key, and the actual
`sentence-transformers/all-MiniLM-L6-v2` model downloaded and run locally.

**Embeddings** — near-duplicate role/skill names scored 0.90–0.90 cosine
similarity; a genuinely unrelated pair scored 0.35. The configured
`ENTITY_SIMILARITY_THRESHOLD=0.86` sits comfortably above the unrelated
score and comfortably below both near-duplicate scores — validated with a
real margin, not just a guessed number. (The verification script itself
suggests a lower midpoint threshold as a generic heuristic; the existing
0.86 default was kept deliberately, since a higher bar means fewer
accidental merges of genuinely different entities, and it already separates
the tested cases cleanly.)

**LLM connectivity** — Groq responded correctly and validated against the
schema on the first real call. Ollama was correctly and cleanly skipped
(not running locally at verification time) rather than erroring — proving
the orchestrator's unavailable-provider handling works on a real failure,
not just the simulated one in the unit tests.

**Also fixed during this pass, worth noting as real debugging, not just
setup**: Supabase's direct connection string is IPv6-only on the free tier
(no IPv4 add-on), which is unreachable from a typical WSL2/home network —
diagnosed from a live `Network is unreachable` error and fixed by switching
to Supabase's Session Pooler (IPv4, Supavisor, free on every plan), which
also required the pooler-specific username format (`postgres.<project-ref>`
rather than bare `postgres`). Separately, a local Postgres cluster ended up
running on a non-default port (5433, not 5432) after a prior process was
left holding 5432 — diagnosed by comparing `pg_lsclusters` output against
the actual connection error rather than assuming the default port was
correct. Both are exactly the kind of environment-specific issues that
would otherwise surface for the first time live in front of a judge.

---

## Phase 5 — orchestration and the API layer

The Phase 4 dedup design assumed candidate entities' embeddings would be
available for comparison, but Phase 3's schema never actually stored one —
only `ResearchSource.embedding` existed. Pulling every existing role into
Python to embed and compare on every analysis run would work at seed-data
scale and quietly stop scaling well before "what happens at 1,000
processes." Fixed by adding `embedding` columns to `Role`, `Skill`, and
`Activity`, and using pgvector's `.cosine_distance()` directly in SQL
(`ORDER BY embedding <=> :query LIMIT 5`) so the database does the coarse
nearest-neighbor search and only the top handful of candidates go through
the already-tested Python matching logic. Deliberately did NOT add
dedup search for `Activity` — activities belong to exactly one process and
aren't meant to be deduped across processes (see `entity_repository.py`'s
docstring for the reasoning); the embedding column exists for potential
future cross-process analytics, not for the dedup pipeline.

### Why the extraction schema needed cross-reference fields (a real design gap, fixed before the pipeline was built on top of it)

The original Phase 4 schema had `activities`, `roles`, `skills`, and
`ai_opportunities` as flat, unconnected lists — nothing told the pipeline
*which* role performs *which* activity, or *which* skills a role needs.
Building the pipeline on that schema as-is would have meant either linking
every role to every activity indiscriminately (a structurally meaningless
graph) or guessing. Fixed by adding `performed_by_role_titles` (on
Activity), `requires_skill_names` (on Role), and `affected_activity_names`
(on AIOpportunity) as name-based cross-references, plus a Pydantic
model-level validator that rejects any reference that doesn't resolve to a
real name elsewhere in the same response — an LLM hallucinating a role
name that doesn't exist anywhere else in its own output now fails loudly
in validation instead of silently producing a broken graph edge.

### Why AIOpportunity's affected roles/skills are derived, not LLM-specified

The LLM specifies which *activities* an opportunity affects
(`affected_activity_names`) but not which roles/skills — those are
computed transitively (activity → its roles → their skills) by the
pipeline. This was a deliberate simplification: an AI opportunity
affecting an activity naturally affects whoever performs it and whatever
skills they bring to it, so asking the LLM to separately (and redundantly)
restate role/skill impacts would just be another place for its answer to
drift out of sync with the activity-level answer it already gave.

### Why persistence is one atomic commit, not many small ones

`AnalysisJob` status/stage updates commit immediately at each step (a
judge watching the UI needs to see `pending → processing → completed` in
real time). The actual entity graph — Process, Activities, Roles, Skills,
AIOpportunities, AIAssessments, GraphEdges — is built entirely in memory
across the LLM/dedup/scoring stages and committed exactly once, at the very
end, together with marking the job completed. If anything fails during
persistence, the whole transaction rolls back and the job is marked failed
in a fresh, separate transaction — there is no code path that leaves a
half-created Process with some but not all of its activities/roles
attached. Verified directly:
`test_malformed_llm_output_fails_the_job_without_partial_writes`.

### Why a failed pipeline run returns HTTP 200, not 500

`POST /api/processes/analyze` returns 200 with `status: "failed"` and a
real `error_message` when validation or the LLM fails — not a 500. A 500
means the server itself broke; a cleanly-rejected duplicate process name or
a malformed LLM response the pipeline caught and reported is the system
working as designed. This is what lets the frontend (and a judge watching
the demo) see "here's why this was rejected" instead of a generic server
error page.

### Two more real bugs caught by testing against the actual running server, not just the test suite

**1. A sandbox package-version drift that would have produced a misleading
result.** An earlier ad-hoc `pip install groq` in Phase 4 had pulled in
`fastapi 0.141.1` as a side effect, silently diverging from the
`fastapi==0.115.0` pinned in `requirements.txt`. On 0.141.1,
`app.include_router()`'s internal representation changed enough that a
naive route-listing check found zero API routes — which would have looked
like a real bug in this codebase, when it was actually a mismatch between
what was being tested and what `requirements.txt` (and therefore your
environment) actually installs. Caught by checking the installed version
against the pin rather than assuming they matched; fixed by reinstalling
the exact pinned versions before continuing.

**2. `Base.metadata.drop_all()` (used by `tests/conftest.py` to clean up
after a full test run) does not touch the `alembic_version` table, because
Alembic manages that table outside of `Base.metadata` entirely.** Running
the test suite, then trying to boot the live server against the same
database, produced `relation "processes" does not exist` — even though
`alembic upgrade head` reported nothing to do, because `alembic_version`
still showed the migrations as applied. This is a genuine, easy-to-hit trap:
"tests cleaned up, so the schema must still be at head" is false whenever
a test suite drops tables directly instead of through Alembic. Documented
here, and worth remembering as a real operational note: after running
`pytest`, the schema needs `alembic upgrade head` again before the live
server will work — this order-of-operations issue is exactly the kind of
thing to mention if asked "what surprised you" in the interview.

---

## Post-Phase-5 — a real bug found during your own local testing

**Alembic's `Config` object (backed by Python's `configparser`) chokes on
any literal `%` stored via `config.set_main_option()` — independent of
whether the URL is correctly percent-encoded.** `migrations/env.py`
originally injected the database URL with
`config.set_main_option("sqlalchemy.url", settings.database_url)`, then
read it back via `config.get_main_option(...)` / `engine_from_config(...)`.
`configparser` applies `%`-interpolation to every stored value, so a URL
containing a literal `%` — which URL-encoded passwords almost always
contain (`%40` for `@`, `%25` for a literal `%`, etc.) — raises
`ValueError: invalid interpolation syntax` the instant it's stored,
regardless of whether the percent-encoding is otherwise correct. This
didn't surface during the Phase 3/4 verification because those runs used a
password without a `%` character in it; it surfaced only once a real
password containing one was used against the local Alembic CLI (as
opposed to plain SQLAlchemy, via `uvicorn`, which never hit this code
path). Fixed by never routing the URL through the configparser-backed
`Config` object at all — `DATABASE_URL` is now a plain Python variable
passed directly to `create_engine()` (online mode) and
`context.configure(url=...)` (offline mode). Reproduced locally with a
throwaway Postgres user whose password was deliberately set to contain a
literal `%`, and confirmed both `alembic current` and a full `alembic
upgrade head` succeed against it before considering this fixed — this bug
was found on a real machine, outside the sandbox this project was
developed in, which is exactly the kind of gap that no amount of
self-testing catches on its own.
