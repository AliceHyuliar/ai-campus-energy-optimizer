# Local frontend–backend integration report

Verified on **2026-11-09** in the existing Windows checkout. All results below were executed during this integration task, except where explicitly described as historical context.

## Git state and verified sources

- Original checkout was clean on `feature/backend-energy`.
- Fetched current remote branch references before integration. `origin/main` and local `main` point to the agreed foundation **9debef0e41177073faa8b7e9cbbf660a7877c9ea**.
- Backend source: **51cfc590f705763a51392d92dd3bfffaae4e59b1**, on local and remote `feature/backend-energy`.
- Frontend source: **8e0c1307af05e001c5da4786a5a0a08b59137b03**, on `origin/feature/frontend-dashboard`.
- Verified open [frontend PR #2](https://github.com/AliceHyuliar/ai-campus-energy-optimizer/pull/2): source `feature/frontend-dashboard`, target `main`, same repository, non-draft, matching the fetched source SHA.
- The GitHub connector could not access this repository. PR metadata was verified with a read-only GitHub API request using existing Git authentication; no credential data was printed or written to project files.
- Both source branches share the agreed foundation. The frontend commit adds four dashboard components and does not modify contracts, schema, examples, or backend files.
- Created `integration/frontend-backend` from the foundation, fast-forwarded the backend, then merged the frontend locally without conflicts. Integration merge: **8be324b78ac274f47569c20e66abaf3a7418264e**. Its parents are the verified backend and frontend source commits.
- Integration fixes and this report are saved only on the local integration branch. Original feature branch tips and `main` are preserved. No branch was pushed, no PR was changed, and no deployment was performed.

## Issues found and integration fixes

1. **The dashboard was never mounted.** The frontend entry point still rendered the original fixture preview. Browser inspection confirmed the preview instead of the new dashboard. Connected the entry point to the existing dashboard component.
2. **The scenario URL was a literal string.** The request contained `${scenario}` rather than the selected ID. Backend logs confirmed 404 requests for that literal value. Added an encoded request helper and removed the TypeScript suppression.
3. **HTTP failures were treated as data.** Added `response.ok` handling, readable errors for contract envelopes and non-JSON proxy failures, and a Retry action. The UI clears old metrics on loading/failure instead of retaining another scenario's values.
4. **Outdated requests could update a newer selection.** Added AbortController cleanup and an active-scenario display guard.
5. **Required simulation/safety context was missing from the mounted dashboard.** Added simulation/estimated/advisory labels, the returned disconnected AI status, class schedule and sensor state, and an explicit stale/missing warning. Null occupancy displays as Unknown; an unknown status uses a warning color. No AI explanation or equipment command was added.
6. **Money displayed without fixed currency precision.** Displayed MYR with two decimal places, preserving the backend value.

No energy rule, power assumption, savings calculation, safety condition, endpoint, response field, shared schema, or fixture was changed.

## Integration-specific file inventory

Modified:

```text
frontend/package.json
frontend/src/main.tsx
frontend/src/App.tsx
frontend/src/Header.tsx
frontend/src/KpiCards.tsx
frontend/src/RoomGrid.tsx
```

Added:

```text
frontend/src/api.ts
frontend/tests/api.test.mjs
scripts/verify_integration.py
docs/INTEGRATION_REPORT.md
```

No frontend or backend feature branch was edited. Integration-specific frontend fixes are contained in this temporary branch. Dependency manifests retain the same dependencies; only an npm test script was added. Screenshots are stored outside the repository in the chat's local visualization directory.

## Newly executed automated checks

| Check | Observed result |
| --- | --- |
| Full backend pytest suite | **175 passed, 1 warning in 1.93s**. |
| Backend Ruff | Passed. |
| Python compilation | Passed for backend and the integration checker. |
| `pip check` | No broken requirements. |
| Frontend TypeScript checks | Passed. |
| Frontend production build | Passed; Vite 7.3.7 generated the dashboard bundle with 33 transformed modules. |
| New frontend API regression tests | **7 passed, 0 failed**. No pre-existing frontend test command was present. |
| Integration checker Ruff | Passed. |
| Real HTTP checker | **22 cases passed**: 11 against FastAPI on port 8000 and the same 11 through Vite on port 5173. |
| Actual frontend request helper over real HTTP | **5 cases passed**: four snapshots matching fixtures and an unknown-scenario 404 propagated as an error. |

The pytest warning is the existing Starlette/httpx TestClient deprecation. Frontend tests use Node's built-in runner and native TypeScript stripping; they were executed with the existing Node 24 environment, with no new test dependency.

The 22 HTTP cases cover health, scenario catalog, four scenario snapshots, missing/repeated query parameters, unknown scenario, unknown route, and unsupported method. All eight successful scenario responses (direct plus proxied) validated against the frozen JSON Schema and matched the approved fixture JSON values. The `Allow: GET` header, AI `not_connected`/null state, and one-classroom scope were checked.

## Scenario results using the real backend

| Scenario | HTTP and UI result | Savings / review count |
| --- | --- | --- |
| `idle-room` | 0 people, fresh sensor, no active class, next class 120 minutes away; AC/lights ON; REVIEW / REVIEW_IDLE_ROOM. | **2.2 kWh / MYR 1.10**, one room needing review. |
| `occupied-room` | 24 people, fresh sensor, active class, next class 90 minutes away; AC/lights ON; NORMAL / NO_ACTION_OCCUPIED. | **0 kWh / MYR 0.00**, zero rooms needing review. |
| `class-soon` | 0 people, fresh sensor, no active class, next class in 10 minutes; AC/lights ON; NORMAL / KEEP_ON_CLASS_SOON. | **0 kWh / MYR 0.00**, zero rooms needing review. |
| `stale-sensor` | Occupancy Unknown, stale sensor warning, next class Unknown; AC/lights ON; UNKNOWN / CHECK_SENSOR_DATA. | **0 kWh / MYR 0.00**, one room needing review. |

All four show one monitored classroom, simulation/estimated labels, and `AI status: not_connected`. No measured savings or real Gemini output is claimed.

## UI interactions actually verified

Used the in-app browser against `http://127.0.0.1:5173/`, supported by backend access logs and independent real HTTP checks. This was not inferred from a successful build or fixture rendering.

- Opened the app before the fixes and observed the original fixture preview.
- Reloaded the connected dashboard and selected all four scenarios with its actual selector.
- Read each rendered result: KPI values/counts, classroom A101, occupancy, sensor status, schedule, enabled equipment, recommendation code/status, and AI disconnection.
- Inspected screenshots of idle, stale-sensor, and error states. Saved full-page idle and stale-sensor evidence outside the repository.
- Verified loading explicitly by stopping FastAPI and temporarily holding a local TCP connection on port 8000. The UI displayed only **Loading metrics...**, with no old room/KPI data. This listener generated no response payload and was used only for failure injection, not as proof of successful backend integration.
- Stopped that listener, leaving the backend unavailable. Vite returned HTTP 500 and the UI displayed a readable alert with a Retry button, without old metrics or fixture fallback.
- Restarted the real FastAPI service and clicked Retry. The dashboard recovered to the real idle-room result, including 2.2 kWh / MYR 1.10.
- Unknown scenario was verified over actual HTTP and through the actual frontend request helper, which rejects the 404 envelope. The selector deliberately exposes only the four approved IDs; arbitrary unknown IDs were not injected into the UI.

Only scenario selection and Retry send HTTP requests. The dashboard contains no equipment-control action, provider connection, or fabricated explanation.

## Reproducing the checks

Start the existing services in separate terminals at the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Run verification (using the existing Node 24 and Python virtual environment):

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m compileall -q backend scripts
.\.venv\Scripts\python.exe -m pip check
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test
.\.venv\Scripts\python.exe scripts/verify_integration.py
```

The verification script makes read-only requests and does not start or stop services itself. Local service processes used for this task were stopped after verification.

## Remaining limitations and recommended merge sequence

- This is a local integration result. GitHub CI remains unconfigured; the new frontend tests run locally through npm. Mobile layouts, additional browsers, and a full accessibility audit were not tested.
- Unsupported backend input combinations documented in `backend/CONTRACT_LIMITATIONS.md` remain outside the four-scenario MVP.
- Gemini Enterprise is still disconnected and requires actual access plus an approved contract change before exposing explanations. No cloud dependencies were introduced.
- The request helper handles network and HTTP errors but has no added timeout policy; a server that never responds can remain loading. Production hosting and broader resilience are outside this local integration task.
- The original frontend PR still contains the entry-point and request bugs; the fixes currently exist only in this local integration branch. The team must review and transfer those fixes into the agreed PR/integration workflow before merging the original frontend implementation.
- Review the integration diff and agree how to carry the tested fixes forward. Once authorized, preserve the source branch histories, incorporate these fixes into the frontend/integration PR, and rerun the checks against the exact proposed merge result. Then review both PRs before merging into `main`. No final merge is performed by this task.
