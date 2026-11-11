# AI Campus Energy & Infrastructure Optimizer

University hackathon prototype. Submission: **2026-11-13 12:00 MYT (UTC+08:00)**.

## Ownership and scope

- Developer A owns `backend/`, simulation, deterministic energy logic, and future AI adapters.
- Developer B owns `frontend/` and dashboard UX.
- `contracts/`, `docs/API_CONTRACT.md`, and this file are shared. Obtain explicit approval before changing another owner's files or shared specifications. The initial common foundation is authorized by the founding request; later changes need agreement.
- Read existing code, contracts, examples, and Git state before editing. Preserve useful work.
- Use `codex/` feature branches in the shared repository. Do not push, merge, deploy, or write to remote resources without explicit approval.

## MVP rules

- React + TypeScript + Vite; Python + FastAPI; HTTP/JSON; JSON Schema contracts.
- `docs/API_CONTRACT.md` is authoritative for HTTP behavior; `contracts/snapshot.schema.json` defines snapshot payloads. Update both together with approval.
- Simulated IoT and classroom data only. Label simulation in UI and payloads. Never control real equipment.
- Unknown, null, missing, or stale occupancy must never be treated as zero occupancy.
- Keep deterministic calculations separate from generative AI. State power, time, tariff, and operational assumptions explicitly.
- Potential savings are estimates, never measured savings.
- Gemini Enterprise access is pending. Do not invent integration or describe mock text as Gemini output. AI remains `not_connected` in this foundation.
- No database, paid cloud dependency, credentials, or additional product features without justification and agreement.
- Do not commit secrets, virtual environments, dependency directories, or generated output.

## Verification and delivery

- Add focused tests for new behavior and validate all four fixtures against the schema.
- Run relevant tests, lint/type checks, and builds. Report actual command results and unresolved failures; never claim unexecuted checks passed.
- Backend: `.venv/Scripts/python -m pytest backend/tests`, `.venv/Scripts/python -m ruff check backend` (Windows); use `.venv/bin/python` on POSIX.
- Frontend: run `npm run lint` and `npm run build` in `frontend/`.
- Report changed files, verified behavior, assumptions, limitations, and next action.
- Stop at the common foundation: fixture-backed endpoints and a fixture preview, without optimization services, a full dashboard, or an AI adapter.
