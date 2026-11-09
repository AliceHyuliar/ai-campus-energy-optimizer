# Developer B handoff: campus overview

The team-approved Phase 2 extension keeps API version 1.0 and the existing fields, endpoints, recommendation codes, errors, and original four snapshot outputs. Backend changes are local on `feature/campus-overview-backend`; this task does not publish a branch or PR.

## Scenario discovery

Fetch `GET /api/v1/scenarios` through the existing Vite `/api` proxy. The response retains `apiVersion`, `dataSource`, and `scenarios`. Each catalog entry has `id`, `name`, and `description`. The original four entries are unchanged, and the fifth entry is:

```json
{
  "id": "campus-overview",
  "name": "Campus overview",
  "description": "Four simulated classrooms with idle, occupied, class-soon, and stale-sensor states."
}
```

Prefer deriving selector values from `id` and labels from `name` rather than adding another hardcoded option. Preserve selection while loading/retrying the catalog, and show catalog failures clearly. The existing frontend selector is intentionally untouched by this backend task and still lists four scenarios.

## Expected response

Request `GET /api/v1/snapshot?scenario=campus-overview`. The complete canonical response is [campus-overview.json](../contracts/examples/campus-overview.json); the authoritative specification is [API_CONTRACT.md](../docs/API_CONTRACT.md) and validation uses [snapshot.schema.json](../contracts/snapshot.schema.json).

The response uses the existing timestamp, a 60-minute analysis window, and MYR 0.50/kWh. Render four room cards in returned order:

| Room | Occupancy | Sensor / schedule | Recommendation | Estimated kWh |
| --- | --- | --- | --- | --- |
| A101 | 0 | fresh, no active class, next in 120 minutes | REVIEW / REVIEW_IDLE_ROOM | 2.2 |
| A102 | 24 | fresh, active class, next in 90 minutes | NORMAL / NO_ACTION_OCCUPIED | 0 |
| A103 | 0 | fresh, no active class, next in 10 minutes | NORMAL / KEEP_ON_CLASS_SOON | 0 |
| A104 | Unknown (null) | stale, no active class, next time unknown | UNKNOWN / CHECK_SENSOR_DATA | 0 |

AC and lights are ON in all four rooms. Preserve each card's equipment/sensor/schedule state independently and use its unique `roomId` as the React key. Existing RoomGrid and KpiCards structures already support this response; no new API fields or layout system are needed.

Use the backend summary directly:

```json
{
  "roomsMonitored": 4,
  "roomsNeedingReview": 2,
  "potentialSavingsKwh": 2.2,
  "potentialSavingsMyr": 1.1
}
```

Display money as **MYR 1.10**. The review count includes both A101 and A104. Do not count only `review`, coerce null occupancy to zero, or recompute money from rounded card values. The backend sums three-decimal room energy estimates and then rounds aggregate money once.

AI remains `{"status":"not_connected","explanation":null}`. Keep simulation, estimated savings, and advisory-only labels. No device-control buttons or AI explanation text should be added.

## Frontend acceptance checks

1. Discover five catalog entries with the original four in the same order, and select campus overview using its actual ID.
2. Confirm the request reaches real FastAPI through Vite, without fixture fallback.
3. Verify exactly four distinct cards, correct room states/codes, 4 monitored / 2 needing review, 2.2 kWh, and MYR 1.10.
4. Confirm A104 displays Unknown occupancy and a stale warning, with zero savings; A102 and A103 must not recommend shutdown.
5. Switch through all four original scenarios and back; retain their original values and clear obsolete cards/KPIs during loading and failures. Test rapid switching and Retry after backend recovery.
6. Verify whole-snapshot HTTP failures display an error rather than partial cards/totals. Missing/unknown scenario errors keep their existing envelopes.
7. Check the four-card desktop/mobile layout, status labels, accessible selector, simulation labels, and disconnected AI state.
8. Run frontend tests, type checks, production build, and joint HTTP/browser verification against the exact proposed merge result.

Older clients that assume a four-entry catalog or validate against the old closed enum must update. No frontend files were modified or new campus UI interactions verified by this backend task. Coordinate a frontend branch/PR after the backend/shared contract changes are made available with approval.
