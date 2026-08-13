# AEGISAI Frontend

React + TypeScript + Tailwind v4 + React Flow + Recharts, talking to the
real FastAPI backend — no mock data anywhere.

## Setup

```bash
npm install
```

The dev server proxies `/api/*` to `http://localhost:8000` (see
`vite.config.ts`) — start the backend first:

```bash
# in backend/, in a separate terminal:
uvicorn app.main:app --reload --port 8000

# then, here:
npm run dev
```

Open http://localhost:5173.

## Production build

```bash
npm run build   # runs tsc -b && vite build, output in dist/
npm run preview # serve the production build locally to sanity-check it
```

**Deployment note:** the API client (`src/api/client.ts`) always calls
relative `/api/...` paths — no backend origin is hard-coded anywhere. This
means production deployment needs the built frontend served from the same
origin as the API (e.g. FastAPI serving `dist/` as static files, or a
reverse proxy routing `/api` to the backend and everything else to the
built frontend). Not yet wired up as a one-command deploy script — see the
architecture decision log for the honest status.

## Design system

Palette, type pairing, and the constellation graph treatment are all
explained in `docs/architecture/decision-log.md` under "Phase 7." Short
version: everything is grounded in the product's own name (Northstar Bank
→ navigation by starlight), not a generic AI-tool template.

## Verification status

TypeScript compiles clean (`tsc -b`), the production build succeeds, and
every API response shape was checked against the real backend (seeded
directly via the ORM, not mocked) — see the decision log for the exact
verification method and why. **Not yet verified**: actual rendering in a
browser. This environment has no browser automation tool, so the checks
above (type-checking against real API responses, successful production
build) are the strongest verification available here — open it yourself
and tell me what needs fixing.
