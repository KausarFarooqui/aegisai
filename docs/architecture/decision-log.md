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
