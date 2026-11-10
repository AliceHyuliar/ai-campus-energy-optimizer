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
| `app/models.py` | Frozen dataclasses for synthetic occupancy, equipment, schedule, scenario metadata, and explicit power assumptions. Strict validation rejects invalid counts, booleans disguised as integers, non-finite tariffs, empty/unstructured collections, invalid rooms in any position, and duplicate room IDs. |
| `app/simulation.py` | Stable five-scenario catalog and structured input loader. Reads only physical state and metadata from the approved examples. Stored analyses, summary totals, and AI fields are ignored and recomputed. IDs are checked before constructing paths. |
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

The authoritative specification is `docs/API_CONTRACT.md`, including the approved Phase 2 extension. The schema only appends `campus-overview` to the scenario enum. All four original examples remain unchanged, and their generated responses retain exact JSON-value parity. The fifth scenario returns four classrooms using the same fields and codes. The following endpoints retain their response shapes, errors, and query validation:

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

## Phase 2 campus overview

`GET /api/v1/scenarios` appends `campus-overview` after the unchanged four original entries. Request `GET /api/v1/snapshot?scenario=campus-overview` for A101 (idle), A102 (occupied), A103 (class soon), and A104 (stale sensor), in that order. The expected summary is **4 monitored**, **2 needing review**, **2.2 kWh**, and **MYR 1.10**. The review count includes the unknown room.

SimulationState accepts a nonempty tuple of valid RoomState objects with unique, case-sensitive IDs. Analysis, calculations, safety rules, and serialization are reused unchanged: decisions are independent per room, energy is summed after per-room rounding, and money is rounded once from the total. One invalid or unsupported room fails the entire snapshot with the existing `FIXTURE_UNAVAILABLE` envelope; no partial result is returned.

The original fixtures and the new `contracts/examples/campus-overview.json` are canonical expected outputs. Schema validation checks structure and safety constraints; backend semantic validation rejects duplicate IDs. No new response fields, status codes, equipment controls, database, dependencies, or AI integration were added.

The current frontend still has its original four-option selector. See [FRONTEND_HANDOFF.md](FRONTEND_HANDOFF.md): Developer B should preferably derive options from the scenarios API and reuse the existing grid and KPI components. The backend/API can be verified independently before frontend work is available.

## Future Gemini Enterprise preparation

`ExplanationProvider.explain(AnalysisReport) -> str` accepts a frozen, provider-independent report containing simulation inputs, assumptions, deterministic decisions, rationales, baseline consumption, and savings estimates. The interface has no model name, external URL, SDK, or authentication assumption. It is not invoked by the request path.

Before enabling an adapter, the team must obtain actual Gemini Enterprise access and its supported integration documentation, decide credential handling and approved data sharing, and define timeout/failure behavior. Credentials must remain outside source control. An explanation must never override deterministic safety decisions or initiate controls. The frozen schema only permits `ai.status = "not_connected"` and `ai.explanation = null`; exposing real explanation output requires an approved shared contract/schema change first. No integration is claimed or performed here.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m compileall -q backend
.\.venv\Scripts\python.exe -m pip check
```

Phase 1 had 175 backend cases. Phase 2 updates scenario-wide tests that assumed one classroom or zero savings for every non-idle scenario. The original fixture content is protected by SHA-256 regression checks and HTTP JSON-value parity tests. The full suite also validates all five examples and generated responses against JSON Schema.

`test_campus_overview.py` covers the exact approved four-room result, five-entry catalog order/content, every-position validation and sensor safety, duplicate IDs, independent decisions, multi-room aggregation, room-order invariance, aggregate rounding, authored-result recomputation, and atomic HTTP failures. In particular, four lighting-only rooms over one minute emit 0.003 kWh each, sum to 0.012 kWh, and produce MYR 0.01, rather than a sum of rounded per-room costs.

With FastAPI on port 8000 and Vite on port 5173, run `.\.venv\Scripts\python.exe scripts/verify_integration.py` for all five scenarios, schema/fixture parity, catalog, health, and error envelopes through both direct HTTP and the proxy. This does not test frontend rendering. Frontend files and tests are outside this backend task.

Starlette's existing httpx TestClient deprecation warning remains a dependency maintenance item. Other unsupported input combinations remain described in [CONTRACT_LIMITATIONS.md](CONTRACT_LIMITATIONS.md). Prepared on `feature/campus-overview-backend` from merged main `082357f`; publishing, PR creation, and merging require separate approval.

Observed Phase 2 verification on **2026-11-09**: **261 passed, 1 warning in 2.19s**. Backend and integration-checker Ruff, Python compilation, and `pip check` passed. **24 real HTTP cases passed** across FastAPI and Vite, including all five snapshots with schema/fixture parity, the catalog, and existing error envelopes. Both test services were stopped afterward. New campus UI rendering was not tested; the frontend handoff is pending Developer B's implementation.

The Phase 2 change inventory is 12 files:

```text
backend/app/models.py
backend/app/simulation.py
backend/tests/test_foundation.py
backend/tests/test_simulation_api.py
backend/tests/test_campus_overview.py                 (new)
backend/README.md
backend/CONTRACT_LIMITATIONS.md
backend/FRONTEND_HANDOFF.md                          (new)
contracts/snapshot.schema.json
contracts/examples/campus-overview.json              (new)
docs/API_CONTRACT.md
scripts/verify_integration.py
```

All frontend files, the four original fixtures, dependencies, and the existing analysis/calculation/rule modules are unchanged. The schema change is limited to the approved scenario enum addition. Current work is local and uncommitted; no push, merge, deployment, or remote resource change was performed.
