# AI Campus Energy & Infrastructure Optimizer

Common foundation for the APU Cloud Innovation Hackathon 2026. Deadline: **November 13, 2026, 12:00 PM MYT (UTC+08:00)**.

This repository contains a React/TypeScript/Vite fixture preview, a FastAPI service serving the same four simulation examples, and a shared JSON Schema. It stops at the foundation: there is no optimizer, full dashboard, live IoT integration, database, equipment control, or Gemini Enterprise connection.

## Layout and ownership

| Path | Purpose / owner |
| --- | --- |
| `frontend/` | Fixture preview and Vite API proxy; Developer B. |
| `backend/` | Fixture-backed API and focused tests; Developer A. |
| `contracts/snapshot.schema.json` | Shared snapshot shape and safety constraints. |
| `contracts/examples/` | `idle-room`, `occupied-room`, `class-soon`, `stale-sensor`. |
| `docs/API_CONTRACT.md` | Authoritative HTTP behavior, units, nulls, errors, and assumptions. |
| `AGENTS.md` | Ownership, scope, and verification rules. |

The founding request authorizes this initial shared foundation. Coordinate later shared specification changes between both developers; use feature branches. Nothing has been pushed or deployed.

## Prerequisites

- Python 3.11 or newer, with pip and venv. The local verification environment uses Python 3.14.
- Node.js 22.12 or newer (or Node 20.19+), and npm. The local environment uses Node 24.
- Run commands from the repository root unless directed otherwise. No cloud account or API key is needed.

## Local setup: Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci
```

Start the backend in one terminal at the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the frontend in another terminal:

```powershell
npm --prefix frontend run dev
```

Open the URL printed by Vite (normally `http://127.0.0.1:5173`). Select any scenario to preview the actual shared example JSON. This works without the backend. The preview deliberately does not fetch HTTP; the proxy is ready for future frontend feature work. Development API docs: `http://127.0.0.1:8000/docs`.

## Local setup: macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal run `npm --prefix frontend run dev`. Virtual environment activation is optional; commands use explicit interpreter paths. To install only the backend runtime, use `backend/requirements.txt`. Frontend versions are locked by `frontend/package-lock.json`. Direct Python dependencies are pinned to verified versions in the requirements files; transitive Python dependencies are not locked.

## Verification

From the repository root, on Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m ruff check backend
npm --prefix frontend run lint
npm --prefix frontend run build
```

On macOS/Linux replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. `lint` is TypeScript strict checking, including unused declarations; no separate ESLint configuration is present. Tests validate the schema itself, all four examples with timestamp format checking, cross-field invariants, unknown-occupancy safety, HTTP fixture parity, and error responses.

With the backend running, smoke test:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/scenarios
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/snapshot?scenario=idle-room'
```

On POSIX, use `curl` with the same URLs. For an optional production bundle preview run `npm --prefix frontend run preview`. The development `/api` proxy is not a production deployment configuration.

## Assumptions and next work

All displayed data is simulation. The idle estimate assumes 2.0 kW AC plus 0.2 kW lighting can be avoided for one hour at MYR 0.50/kWh, with a 15-minute preconditioning buffer before the next class: **2.2 kWh / MYR 1.10 potential savings**, never measured savings. Stale/missing/null occupancy is unknown; it earns no savings credit. See the API contract for all field semantics.

Gemini Enterprise access is pending; `ai.status` is `not_connected` and `ai.explanation` is null. No AI-generated output is presented. Keep future deterministic calculations separate from AI explanation code.

Next, both developers should review and freeze the initial contract, then build the deterministic simulator and dashboard in separate feature branches. No remote URL is configured in the initial checkout; adding a remote, pushing, merging, and deployment require explicit approval. Keep credentials in local ignored files, never in source or fixtures.
