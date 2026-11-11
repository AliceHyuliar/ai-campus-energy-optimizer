# Common foundation delivery

Verified locally on **2026-11-09**, on Windows with Python **3.14.0**, Node **24.20.0**, and npm **11.19.0**.

## Repository inspection and scope

The initial checkout contained only `.git`: no tracked files, starter pack, schema, examples, documentation, commits, or configured remote. Work is on local branch `codex/common-foundation`. No commit, push, merge, deployment, or remote-resource change was performed.

The common foundation is complete. The API reads fixed examples, and the frontend previews those examples directly. No deterministic optimizer, live data pipeline, complete dashboard, equipment control, AI adapter, or database was implemented.

## Created files

```text
.gitignore
AGENTS.md
README.md
backend/__init__.py
backend/app/__init__.py
backend/app/main.py
backend/pyproject.toml
backend/requirements.txt
backend/requirements-dev.txt
backend/tests/test_foundation.py
contracts/snapshot.schema.json
contracts/examples/idle-room.json
contracts/examples/occupied-room.json
contracts/examples/class-soon.json
contracts/examples/stale-sensor.json
docs/API_CONTRACT.md
docs/FOUNDATION_STATUS.md
frontend/index.html
frontend/package.json
frontend/package-lock.json
frontend/tsconfig.json
frontend/vite.config.ts
frontend/src/main.tsx
frontend/src/style.css
```

Local `.venv/`, `frontend/node_modules/`, `frontend/.npm-cache/`, and `frontend/dist/` were generated for verification and are ignored by Git. `.env` and `.env.local` ignore behavior was checked as well.

## Observed verification

| Check | Result |
| --- | --- |
| `python -m pytest backend/tests -q` using the local venv | **24 passed**, one upstream deprecation warning. |
| JSON Schema meta-validation and all four examples | Passed as part of pytest, including date-time format validation. |
| Summary totals, estimate assumptions, unknown-occupancy constraints, fixture parity, and API errors | Passed as part of pytest. |
| `python -m ruff check backend` using the local venv | Passed after correcting initial line-length/import configuration issues. |
| `python -m compileall -q backend` using the local venv | Passed. |
| `python -m pip check` using the local venv | No broken requirements. |
| `npm --prefix frontend run lint` | Passed TypeScript strict/unused checks. |
| `npm --prefix frontend run build` | Passed, Vite 7.3.7 production bundle generated. |
| Live Uvicorn HTTP smoke | Health/catalog and all four snapshot fixtures passed; missing scenario returned 400 and unknown scenario returned 404. |
| Live Vite HTTP smoke | HTML and transformed React module returned 200; API proxy returned stale-sensor data with null occupancy preserved. |

Initial dependency downloads failed under restricted DNS, and local HTTP/event-loop checks were blocked by sandbox socket restrictions. Approved execution outside those restrictions completed the checks. The temporary HTTP servers were stopped after smoke testing. Browser rendering and scenario selection were not visually or interactively reviewed.

## Assumptions and remaining limitations

- The supplied snapshot fields were retained. The initial contract adds `snapshotAt` as an explicit UTC simulated reference instant; there was no prior schema to overwrite.
- Fixture time is fixed at `2026-11-09T00:00:00Z`; sensor freshness is an authored categorical state, not derived from the current clock.
- Idle potential savings assume 2.0 kW AC plus 0.2 kW lighting avoided for 60 minutes at MYR 0.50/kWh, with a 15-minute preconditioning buffer: 2.2 kWh and MYR 1.10. These are synthetic estimates, not measurements.
- Stale/missing/null occupancy is unknown and earns no savings credit. No real equipment is addressed or controlled.
- Gemini Enterprise access is pending. AI reports `not_connected` with a null explanation.
- Starlette's TestClient warns that its httpx integration is deprecated in favor of httpx2. Tests pass; migrating test transport can be evaluated during backend feature work.
- Direct Python dependencies are pinned, but Python transitive dependencies are not locked. The frontend has an npm lockfile.
- Browser API integration, a decision engine for arbitrary input combinations, and production hosting remain outside this foundation. Standard JSON Schema cannot enforce cross-field sums or field-to-field comparisons; fixture semantic tests cover those invariants.

## Recommended next action

Both developers should review and agree to freeze `docs/API_CONTRACT.md` and `contracts/snapshot.schema.json`, then start separate feature branches for deterministic backend logic and frontend dashboard work. Shared changes require explicit agreement. Remote setup, pushes, merges, and deployment still require approval.
