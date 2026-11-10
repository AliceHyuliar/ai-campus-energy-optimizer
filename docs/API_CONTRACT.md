# Campus Energy HTTP API v1.0

This is the authoritative HTTP specification, including the team-approved Phase 2 `campus-overview` extension. Payload validation uses `contracts/snapshot.schema.json` (JSON Schema Draft 2020-12). The original four examples and their JSON-value outputs are preserved. Later shared changes require both developers' agreement. `apiVersion` remains the string `"1.0"`.

## Transport

- Local base URL: `http://127.0.0.1:8000`. Responses are JSON with `Content-Type: application/json`.
- The three product endpoints support GET only. There is no authentication, database, equipment control, streaming, or AI invocation.
- The Vite development server proxies relative `/api` requests to port 8000. Cross-origin access is not configured; use the proxy for browser API work.
- Query values are case-sensitive. Unrecognized query keys are ignored. `scenario` must occur exactly once on the snapshot endpoint.
- FastAPI's local `/docs`, `/redoc`, and `/openapi.json` are development aids; this document defines the product contract and error responses.

## GET /api/health

200:

```json
{"status":"ok","apiVersion":"1.0","dataSource":"simulation"}
```

All three string fields are required. `ok` means the HTTP process is responding, not that fixtures, sensors, AI, or cloud services have been checked.

## GET /api/v1/scenarios

200:

```json
{
  "apiVersion": "1.0",
  "dataSource": "simulation",
  "scenarios": [
    {"id":"idle-room","name":"Idle room","description":"Fresh zero occupancy; AC and lights remain on."},
    {"id":"occupied-room","name":"Occupied room","description":"An occupied classroom with a class in session."},
    {"id":"class-soon","name":"Class soon","description":"An empty room with a class starting in 10 minutes."},
    {"id":"stale-sensor","name":"Stale sensor","description":"Occupancy is unknown because its sensor is stale."},
    {"id":"campus-overview","name":"Campus overview","description":"Four simulated classrooms with idle, occupied, class-soon, and stale-sensor states."}
  ]
}
```

All fields are required. Each scenario has string `id`, `name`, and `description`; IDs are unique. The original four entries retain their values and order; `campus-overview` is appended fifth. Consumers should key by ID and preferably derive selector options from this endpoint.

## GET /api/v1/snapshot?scenario=<id>

Required query: one non-empty `scenario` string from the five IDs above. No default scenario; surrounding whitespace is not trimmed into a valid ID. On 200, the computed response has JSON-value parity with the corresponding approved example in `contracts/examples/`. Objects have no additional properties. Every field below is required, including nullable fields.

| Field | Type / units | Meaning |
| --- | --- | --- |
| `apiVersion` | string, `"1.0"` | Shared payload version. |
| `scenarioId` | scenario ID string | Exactly matches the request. |
| `dataSource` | string, `"simulation"` | All data is synthetic. |
| `snapshotAt` | UTC RFC 3339 string | Exact `YYYY-MM-DDTHH:mm:ssZ` format, no fractions or other offsets. Simulated reference instant, not response time. |
| `analysisWindowMinutes` | integer, 1–1440 minutes | Forward estimate window starting at `snapshotAt`. |
| `tariffMyrPerKwh` | nonnegative number, MYR/kWh | Assumed flat electricity tariff. |
| `summary.roomsMonitored` | positive integer | Number of room entries. |
| `summary.roomsNeedingReview` | nonnegative integer | Count of rooms whose status is `review` or `unknown`. |
| `summary.potentialSavingsKwh` | nonnegative number, kWh | Sum of the room estimates. |
| `summary.potentialSavingsMyr` | nonnegative number, MYR | Total kWh × tariff, rounded to two decimals, half up. |
| `rooms` | nonempty array | Room IDs must be unique within a snapshot. |
| `rooms[].roomId` | nonempty string, ≤64 characters | Simulated room identifier. |
| `rooms[].occupancy` | nonnegative integer or null, people | `0` is confirmed empty only with fresh data; null means unknown. |
| `rooms[].sensorStatus` | `fresh`, `stale`, or `missing` | Supplied simulation state, not derived from wall-clock time. Stale/missing requires null occupancy. |
| `rooms[].classInSession` | boolean | Simulated schedule flag, never inferred from occupancy. |
| `rooms[].minutesToNextClass` | nonnegative integer or null, minutes | Delay from `snapshotAt`; 0 means starting now, null means the next class time is unknown. Null does not prove the room is free. |
| `rooms[].devices.acOn` | boolean | Simulated AC state. |
| `rooms[].devices.lightsOn` | boolean | Simulated lighting state. |
| `rooms[].analysis.status` | `review`, `normal`, or `unknown` | Advisory state; never an equipment command. |
| `rooms[].analysis.recommendationCode` | enum below | Machine-readable advisory. |
| `rooms[].analysis.potentialSavingsKwh` | nonnegative number, kWh | Documented estimate; zero on normal/unknown rooms. |
| `ai.status` | string, `"not_connected"` | Gemini Enterprise access is pending; no adapter exists. |
| `ai.explanation` | null | No generated or mock AI explanation. |

`null` is distinct from zero and false; never omit a required field or coerce unknown occupancy to zero. Fresh sensors may still have null occupancy; this also requires `unknown` analysis. JSON numbers must be finite, not numeric strings. Energy estimates are rounded to three decimal places, half up; money to two. Trailing zeros are not significant in JSON.

| Recommendation | Required status | Fixture meaning |
| --- | --- | --- |
| `REVIEW_IDLE_ROOM` | `review` | Fresh occupancy 0, no active class, at least one device on, known next class at least the full analysis window plus 15 minutes away. Human review only. |
| `NO_ACTION_OCCUPIED` | `normal` | Fresh occupancy >0; retain current equipment state. |
| `KEEP_ON_CLASS_SOON` | `normal` | Fresh occupancy 0, no current class, next class in 0–15 minutes inclusive; retain current state. |
| `CHECK_SENSOR_DATA` | `unknown` | Null occupancy; no energy reduction is assumed. |

The schema enforces shapes, types, enum pairings, and safety constraints for occupancy. Unique room IDs, totals, rounding, and the cross-field comparison `minutesToNextClass >= analysisWindowMinutes + 15` are semantic rules enforced by the backend and/or checked by focused tests, because standard JSON Schema does not compare fields. The API exposes five approved fixed simulations; it does not accept arbitrary room inputs. The existing recommendation vocabulary still cannot express all possible input combinations.

## Simulation assumptions and estimates

All fixtures use `snapshotAt = 2026-11-09T00:00:00Z` (08:00 MYT), a 60-minute window, and MYR 0.50/kWh. These are synthetic fixed inputs; their age does not change sensorStatus. `fresh`, `stale`, and `missing` are categorical fixture states; no sensor TTL or live sensor protocol is defined yet.

- The four original scenarios each contain one room, A101. The campus scenario contains four rooms. Assumed constant demand per classroom is AC **2.0 kW**, lighting **0.2 kW**.
- Baseline: the enabled devices would remain on throughout the window.
- Idle case: assume both devices could be off for all 60 minutes after a human reviews the situation. Next class is 120 minutes away, beyond the 60-minute window plus the assumed **15-minute preconditioning buffer**.
- Estimated upper-bound avoided energy = `(2.0 + 0.2) kW × (60 / 60) h = 2.2 kWh`; estimated cost = `2.2 × 0.50 = MYR 1.10`.
- Occupied case: 24 people, class active, next class in 90 minutes; zero assumed reduction.
- Class-soon case: confirmed empty, next class in 10 minutes; zero assumed reduction to preserve preconditioning.
- Stale-sensor case: occupancy and next class time unknown; zero assumed reduction. This means no savings are credited, not proof of no waste.

These are fixture estimates, never measured savings. No HVAC cycling, weather, comfort model, demand charge, sensor validation, or optimization algorithm is present. A future deterministic calculator must make assumptions explicit and remain independent of any generative AI adapter.

## Campus overview and multi-classroom semantics

`GET /api/v1/snapshot?scenario=campus-overview` returns exactly four classrooms in stable A101, A102, A103, A104 order. The complete expected response is `contracts/examples/campus-overview.json`. It uses the same timestamp, 60-minute window, tariff, power assumptions, and preconditioning buffer as the original examples. All four rooms have AC and lights ON.

| Room | Occupancy / sensor | Active class / next class | Status / recommendation | Estimated savings |
| --- | --- | --- | --- | --- |
| A101 | 0 / fresh | false / 120 minutes | review / REVIEW_IDLE_ROOM | 2.2 kWh |
| A102 | 24 / fresh | true / 90 minutes | normal / NO_ACTION_OCCUPIED | 0 kWh |
| A103 | 0 / fresh | false / 10 minutes | normal / KEEP_ON_CLASS_SOON | 0 kWh |
| A104 | null / stale | false / null | unknown / CHECK_SENSOR_DATA | 0 kWh |

```json
{
  "roomsMonitored": 4,
  "roomsNeedingReview": 2,
  "potentialSavingsKwh": 2.2,
  "potentialSavingsMyr": 1.1
}
```

- A snapshot contains one or more valid rooms with unique, case-sensitive `roomId` values. The original four examples remain single-room snapshots; the new approved example contains exactly four. No maximum count or new public room-input endpoint is introduced.
- Each room's occupancy, sensor, equipment, schedule, recommendation, and savings are evaluated independently. One eligible room never makes another room eligible.
- Snapshot-level timestamp, analysis window, and tariff apply to every room; no per-room tariff/time fields are added.
- `roomsMonitored` is the number of rooms. `roomsNeedingReview` counts both `review` and `unknown`; campus overview therefore counts A101 and A104.
- Round each room's energy estimate half up to three decimal places. Sum those emitted estimates using Decimal arithmetic. Multiply the aggregate by the tariff and round money half up to two places. Do not sum individually rounded room costs. Zero credit for unknown occupancy is not proof of zero waste.
- Room order follows the authored input order. Duplicate IDs are rejected, not merged or deduplicated. Schema `uniqueItems` alone cannot enforce unique IDs across different room objects.
- Validation and analysis are atomic for the whole snapshot. Empty/invalid room collections, any invalid room, duplicate IDs, or any unsupported recommendation input combination make the simulation source unavailable. The API returns the existing 500 `FIXTURE_UNAVAILABLE` envelope; it does not skip rooms or return partial totals.
- AI remains `not_connected` with a null explanation. Recommendations remain advisory; no real equipment state is changed.

This is an additive extension within API version 1.0. Existing snapshot requests, fields, types, recommendation codes, and errors retain their behavior. The scenario catalog now has five entries. Older validators with a closed four-value scenario enum must adopt the approved schema before accepting `campus-overview`.

## Errors

All application errors use the same required two-field object; no additional error fields:

```json
{"error":{"code":"UNKNOWN_SCENARIO","message":"Unknown scenario. See /api/v1/scenarios."}}
```

| HTTP status | `error.code` | Trigger / exact message |
| --- | --- | --- |
| 400 | `INVALID_QUERY` | Missing, empty, whitespace-only, or repeated scenario: `Provide exactly one non-empty scenario parameter.` |
| 404 | `UNKNOWN_SCENARIO` | Nonempty unrecognized ID (including wrong case or whitespace around an ID): `Unknown scenario. See /api/v1/scenarios.` |
| 404 | `NOT_FOUND` | Unknown route: `Route not found.` |
| 405 | `METHOD_NOT_ALLOWED` | Unsupported method: `Method not allowed.` The standard `Allow` header is retained. |
| 500 | `FIXTURE_UNAVAILABLE` | Simulation source cannot be read, parsed, validated, or fully analyzed using the approved codes: `Simulation fixture is unavailable.` |

The error envelope has a required object `error` containing string `code` and string `message`. Branch on `code`, display `message` as plain text. Infrastructure failures are outside this local application contract. No secrets, filesystem paths, or exception traces are returned in fixture errors.

## Working independently

Developer B can use the approved JSON examples independently or call relative `/api/v1/...` URLs through Vite. Prefer the scenarios endpoint for selector options and render every entry in `rooms`. The existing room grid and KPI components already accept arrays and aggregate summaries. See `backend/FRONTEND_HANDOFF.md` for the Phase 2 handoff. Tests validate fixture parity and error behavior. Do not add fields, change null meanings, or claim Gemini integration without a reviewed contract change.
