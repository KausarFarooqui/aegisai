# AEGISAI — Demo Script (10-15 minutes)

Written against the app as it actually exists right now, not an earlier
plan. Rehearse this once end-to-end before the real thing; timings are
approximate, adjust to your own pace.

## Before you start

```bash
# Terminal 1
cd ~/projects/aegisai/backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd ~/projects/aegisai/frontend
npm run dev
```
Open http://localhost:5173. Confirm the Dashboard shows real numbers
(10+ processes) before anyone's watching -- if it shows zeros, your .env
is pointing at the wrong database (should be Supabase, not local).

---

## 1. Open with the business problem (30 seconds)

"This is AEGISAI, built for MODUS Assignment 11 -- a Process x Role x
Skill Intelligence Graph for a fictional retail bank, Northstar Bank.
The question it answers: when a bank introduces AI, which activities
change, which roles are affected, which skills matter more or less, and
what should the organization do about it -- navigable, not a static
report."

## 2. Executive Dashboard (1-2 minutes)

Point at the KPI strip -- processes, activities, roles, skills, AI
opportunities, high-impact count. "These aren't sample numbers -- this is
a live count from Postgres."

Point at "Most affected roles" -- "Loan Underwriter shows up here because
it's genuinely linked to the most AI opportunities across the whole graph
-- that's a real aggregate query, not a hand-picked example."

## 3. Intelligence Graph -- 2D (2 minutes)

Navigate to Intelligence Graph, select a process from the dropdown.

"Every node here is a real database row. Gold stars are AI
opportunities -- everything else is process, activity, role, or skill,
color-coded." Click a node -- "clicking navigates the graph to that
node's own neighborhood, so you can walk Process -> Activity -> Role ->
Skill in either direction."

## 4. Intelligence Graph -- 3D (1-2 minutes)

Click the 3D toggle, top right. Orbit with drag, zoom with scroll.

"Same data, rendered as a real WebGL scene -- AI opportunities are actual
glowing sprites, not just colored dots, so they read as points of light
from any angle."

## 5. Process detail + explainable scoring (2 minutes)

Click into a process from the graph or the Processes list. Expand an
activity with an AI opportunity attached.

Point at the score breakdown: "This score isn't the LLM's opinion -- it's
a fixed weighted formula: 30% repetitiveness, 20% data availability, 20%
predictability, 15% digitalization, 15% AI capability fit. The LLM
proposes the five inputs with reasons; deterministic code computes
everything from there. That split is the actual answer to 'how do you
stop the AI from just making up a score.'"

## 6. Role and Skill intelligence (1-2 minutes)

Click into a role from the activity -- show its required skills, each with
a trend badge (Increasing/AI-Augmented/etc.). Click into a skill -- show
the trend rationale text. "This isn't a label someone typed -- it's
recomputed from every AI opportunity actually linked to this skill,
every time the graph changes."

## 7. The Surprise Record Test -- live (3-4 minutes, the centerpiece)

Navigate to Analyze New Process. Type in something genuinely not in
the seed set -- ask the judge for a process name if they'll give you one,
or use something like "Fraud Alert Investigation."

"This is going to make one real call to Groq right now -- not a script,
not a canned response." Let it run (10-30 seconds) -- narrate while it
works: "extracting activities and roles now... scoring the AI
opportunities... this exact mechanism is what seeded all 10 of the other
processes too -- there's no separate 'demo path.'"

When it completes, click View process, then View in graph --
"and now it's part of the same graph as everything else, immediately."

If you want the strongest possible moment here: run a second analysis
with a process that would plausibly reuse a role/skill from the first
(e.g., anything mentioning "credit" or "compliance" again) -- if the same
role gets reused instead of duplicated, point at the fact that Groq had
no memory of the first call. That's the dedup mechanism working on two
genuinely independent LLM calls, live.

## 8. Architecture, briefly (1-2 minutes)

"Backend: FastAPI, PostgreSQL via Supabase, pgvector for semantic
search. AI layer: Groq as primary LLM with a local Ollama fallback if
Groq's ever unavailable, and local embeddings so there's zero external
dependency for the dedup mechanism itself. Everything free-tier, nothing
here needs a paid license to run."

If asked "why Postgres over a graph database" or similar architecture
questions -- full reasoning is in docs/architecture/decision-log.md,
worth having open in a tab.

## 9. Close with honesty, not overclaiming (1 minute)

"A few things I'd build next, not because they're missing by accident:
a natural-language query interface over this same data, automated
frontend tests, and a couple of MODUS's suggested pages I deliberately
scoped out to keep what's here genuinely working rather than spread
thin." -- Full list in docs/architecture/quality-gate-audit.md.

---

## If something breaks live

- Dashboard shows zeros: backend's .env isn't pointing at Supabase -- restart uvicorn after fixing.
- Analyze hangs past ~40s: Groq rate limit -- the fallback to Ollama should kick in automatically; if Ollama isn't running locally, it'll fail cleanly with a real error message, not a crash. Worth explaining that as the fallback design working as intended, not a bug.
- 3D graph looks wrong: fall back to the 2D toggle -- both show the same real data, and you already know 2D works.
