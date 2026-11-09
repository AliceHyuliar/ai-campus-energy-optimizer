# Deterministic backend MVP

Run from the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

On POSIX use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`. Create the venv first if necessary, as described in the root README. No dependencies were added for this implementation.

## Architecture

| Module | Responsibility |
| --- | --- |
| `app/models.py` | Frozen dataclasses for synthetic occupancy, equipment, schedule, scenario metadata, and explicit power assumptions. Strict validation rejects invalid counts, booleans disguised as integers, non-finite tariffs, and unsupported room counts. |
| `app/simulation.py` | Stable four-scenario catalog and structured input loader. Reads only physical state and metadata from the approved examples. Stored analyses, summary totals, and AI fields are ignored and recomputed. IDs are checked before constructing paths. |
| `app/schedule.py` | Relative schedule evaluation: active class, starts within buffer, full clear window, unknown time, or window conflict. No wall-clock reads. |
| `app/energy.py` | Pure Decimal calculations for enabled-device baseline consumption, eligible avoided energy, and estimated cost. |
| `app/rules.py` | Safe advisory decisions and deterministic human-readable rationales. Uses only frozen status/code values. |
| `app/analysis.py` | Immutable structured reports and public snapshot assembly. Internal baseline consumption, rationales, and assumptions are not added to the response schema. |
| `app/ai.py` | Provider-independent `ExplanationProvider` protocol and disconnected public AI state. No provider implementation, credential lookup, network call, or substitute AI. |
| `app/routes.py`, `app/errors.py`, `app/main.py` | Thin API routes, unchanged error envelope/messages, and application assembly. |

The input source remains `contracts/examples/`. These files are simulation seeds and parity references; output analyses are no longer served from their precomputed fields. The original missing-source behavior remains available through the existing `main.CONTRACTS_DIR` path. There is no separate copied data file to drift from the shared examples.

## Calculations and safety

- Defaults: AC **2.0 kW**, lights **0.2 kW**, window **60 minutes**, tariff **MYR 0.50/kWh**, buffer **15 minutes**. The buffer is fixed because the public recommendation semantics depend on it. Power assumptions are explicit internal values; no HTTP configuration was added.
- Enabled equipment consumption = `(enabled AC kW + enabled lighting kW) × window minutes / 60`. This is an estimated constant-demand baseline, not a meter reading.
- Only `REVIEW_IDLE_ROOM` receives a savings credit for the full analysis window. Fresh occupancy must be exactly zero, no class may be active, at least one device must be on, and the known next class must start at least `window + 15` minutes later. This produces **2.2 kWh / MYR 1.10** for the idle-room example.
- Occupied, class-soon, and unknown-occupancy cases receive zero credited savings. Their estimated baseline consumption can still be positive internally.
- Energy rounds half up to three places. Cost uses the emitted rounded energy and tariff, rounding half up to two places. Summary energy sums room estimates; summary cost uses that sum, not a sum of individually rounded costs.
- Fresh null occupancy remains unknown. Stale or missing sensors invalidate any reported count, including zero; serialized occupancy becomes null. Missing required fields fail validation rather than defaulting to zero.
- Schedule times are relative to the fixed simulated snapshot. A class at 0 or 15 minutes is protected; at 75 minutes the default full 60-minute window plus buffer is available. Active classes take precedence over upcoming times.
- Dataclasses and reports are immutable. Decisions produce advisory text only. There are no command publishers or equipment-control APIs.

See [CONTRACT_LIMITATIONS.md](CONTRACT_LIMITATIONS.md) for combinations the frozen code set cannot express. No new recommendation or HTTP error codes were invented.

## API and frontend integration

The authoritative specification remains `docs/API_CONTRACT.md`; its schema and four examples are unchanged. All four generated responses retain JSON-value parity with their examples, one classroom per scenario. The following endpoints retain their response shapes, errors, and query behavior:

```text
GET /api/health
GET /api/v1/scenarios
GET /api/v1/snapshot?scenario=<id>
```

The frontend can continue importing the shared JSON examples independently. For live simulation results, run the backend on port 8000 and use the existing Vite proxy:

```typescript
const response = await fetch(`/api/v1/snapshot?scenario=${encodeURIComponent(scenarioId)}`);
const payload = await response.json();
if (!response.ok) throw new Error(payload.error.message);
// payload has the unchanged snapshot contract; occupancy may be null.
```

Keep simulation labels and the distinction between estimated and measured savings. Render nullable occupancy as unknown, never zero. No frontend files were modified. There is no deployment configuration or cross-origin configuration change.

## Future Gemini Enterprise preparation

`ExplanationProvider.explain(AnalysisReport) -> str` accepts a frozen, provider-independent report containing simulation inputs, assumptions, deterministic decisions, rationales, baseline consumption, and savings estimates. The interface has no model name, external URL, SDK, or authentication assumption. It is not invoked by the request path.

Before enabling an adapter, the team must obtain actual Gemini Enterprise access and its supported integration documentation, decide credential handling and approved data sharing, and define timeout/failure behavior. Credentials must remain outside source control. An explanation must never override deterministic safety decisions or initiate controls. The frozen schema only permits `ai.status = "not_connected"` and `ai.explanation = null`; exposing real explanation output requires an approved shared contract/schema change first. No integration is claimed or performed here.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m compileall -q backend
```

`test_foundation.py` is preserved unchanged. New tests cover recomputation from physical inputs, original fixture parity and schema validation, consumption and rounding, sensor/schedule safety boundaries, summary totals, unsupported combinations, invalid sources/IDs, response isolation, HTTP compatibility, and AI disconnection. Starlette's existing httpx TestClient deprecation warning remains a dependency maintenance item.

Observed locally on **2026-11-09**: **175 passed, 1 warning in 1.56s** (the original 24 plus 151 new cases). Ruff, Python compilation, and `pip check` passed. A temporary real Uvicorn server passed health/catalog, all four computed snapshots with fixture parity and JSON Schema validation, and 400/404/405 error compatibility checks; it was stopped afterward. No new dependencies were installed.

The complete change inventory is 15 backend files: modified `app/main.py`; added `app/models.py`, `app/simulation.py`, `app/schedule.py`, `app/energy.py`, `app/rules.py`, `app/analysis.py`, `app/ai.py`, `app/errors.py`, `app/routes.py`, `tests/test_energy.py`, `tests/test_safety.py`, `tests/test_simulation_api.py`, this `README.md`, and `CONTRACT_LIMITATIONS.md`. Shared specifications, examples, frontend files, requirements, and the original foundation tests are unchanged. All implementation changes remain local and uncommitted on `feature/backend-energy`.
