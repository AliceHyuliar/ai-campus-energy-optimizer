# AI Campus Energy & Infrastructure Optimizer

APU Cloud Innovation Hackathon 2026 prototype. A React and TypeScript dashboard uses a FastAPI backend to analyze simulated classroom occupancy, schedules, and equipment states. The API supplies five options in the scenario picker. Choose **Idle room**, **Occupied room**, **Class soon**, **Stale sensor**, or **Campus overview**.

## Prerequisites

- Verified on Windows and Ubuntu (WSL) with **Python 3.14.0** and **Node.js 24.20.0**. Use Python with `pip` and `venv`, and Node.js with `npm`.
- On Debian or Ubuntu, install `python3-venv` for the system Python if `python3 -m venv` reports that `ensurepip` is unavailable. For a separately installed Python version, use its matching `venv` package.
- Clone or download this repository and run every command from its root. `backend/requirements-dev.txt` includes the backend runtime and test dependencies. `npm ci` installs the frontend dependencies from the lockfile.
- Local use requires no cloud account or API key.

## Install dependencies

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci
```

**macOS / Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci
```

## Run the application

**Terminal 1 — FastAPI on port 8000**

Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

macOS / Linux

```sh
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Vite on port 5173**

```sh
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Open [the dashboard](http://127.0.0.1:5173/) with both terminals running. The browser requests relative `/api` URLs on port 5173, and Vite forwards those requests to FastAPI at `http://127.0.0.1:8000`. This proxy is for local development.

## Quick smoke test

Choose **Campus overview** (`campus-overview`) in the scenario picker. Expect four classrooms (**A101–A104**), **2 rooms needing review**, and estimated potential savings of **2.2 kWh** and **MYR 1.10**. A104 should show **Unknown** occupancy and a stale sensor warning.

You can also open the [campus snapshot through the Vite proxy](http://127.0.0.1:5173/api/v1/snapshot?scenario=campus-overview) and inspect its `rooms` and `summary` fields.

## Run verification

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m ruff check backend
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python` in the Python commands. The frontend lint command runs the TypeScript checker.

With both servers running, run the HTTP integration check from a third terminal.

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe scripts/verify_integration.py
```

**macOS / Linux**

```sh
.venv/bin/python scripts/verify_integration.py
```

The integration script runs 24 checks across FastAPI and the Vite proxy. It covers health, the scenario catalog, all five snapshots against the shared schema and examples, and API error responses.

## Simulation and safety

All classroom and energy data are simulated. The campus estimate assumes 2.0 kW of AC and 0.2 kW of lighting for one eligible hour at MYR 0.50/kWh. The system collects no energy measurements. Recommendations are advisory and do not control physical equipment. Gemini Enterprise is disconnected, and the API reports `ai.status` as `not_connected`.

See the [API contract](docs/API_CONTRACT.md), [snapshot schema](contracts/snapshot.schema.json), and [scenario examples](contracts/examples/).
