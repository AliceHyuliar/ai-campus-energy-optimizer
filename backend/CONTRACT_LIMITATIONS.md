# Frozen contract gaps for team discussion

This records limitations; it does not amend `docs/API_CONTRACT.md`, the schema, examples, or response codes. The four approved scenarios are representable without changes and still contain exactly one classroom each.

## Input combinations without an honest existing advisory

With fresh occupancy exactly zero, the frozen vocabulary cannot describe all safe retain-state situations:

| Input combination | Why existing codes cannot express it |
| --- | --- |
| A class is active | `NO_ACTION_OCCUPIED` requires occupancy greater than zero. Both idle-review and class-soon codes require no active class. `CHECK_SENSOR_DATA` requires null occupancy. |
| Next class time is unknown | Null schedule data is not proof of a free window. The sensor-check code would misrepresent confirmed zero occupancy. |
| Next class is 16–74 minutes away with the default window | The 15-minute class-soon code does not apply, and the full 60-minute estimate plus 15-minute buffer is unavailable. Partial-window savings are outside the agreed full-window semantics. |
| All devices are off and no class starts soon | There is no idle equipment waste to review; the idle-review code requires at least one enabled device. |

The engine raises internal `ContractLimitation` for these cases, producing no recommendation or savings report. If a locally edited seed introduces one, the API treats that simulation source as unavailable and returns the existing 500 `FIXTURE_UNAVAILABLE` envelope, without exposing internal details or inventing a response code. No HTTP endpoint accepts arbitrary room inputs, and the four approved examples do not trigger this behavior.

## Decisions requiring future team approval

- Agree how to express a safe retain-state/no-waste decision, active schedule conflicts, and unknown schedules while preserving actual occupancy. No new code names are defined here.
- Decide whether to support partial-window savings, including the schedule, comfort, and preconditioning assumptions. Current calculations credit a full eligible window only.
- Decide whether and how to expand classroom counts. The input model currently rejects anything other than one classroom; no extra rooms were added.
- Decide how baseline consumption, deterministic rationale text, and actual AI explanations could be exposed. They remain internal because the schema has no fields for the first two and requires a disconnected AI state.

Do not reinterpret existing codes, replace unknown occupancy with zero, hide confirmed occupancy as null to fit a code, or add HTTP statuses/fields without shared approval. These gaps do not block frontend use of the existing four scenarios.
