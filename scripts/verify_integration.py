"""Read-only HTTP checks against the running FastAPI service and Vite proxy.

Run from the repository root: .venv/Scripts/python scripts/verify_integration.py
Requires the existing backend development dependencies and both local services.
"""

import json
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Draft202012Validator(
    json.loads((ROOT / "contracts/snapshot.schema.json").read_text("utf-8")),
    format_checker=FormatChecker(),
)
SCENARIOS = ("idle-room", "occupied-room", "class-soon", "stale-sensor")


def verify() -> None:
    checked = 0
    for base in ("http://127.0.0.1:8000", "http://127.0.0.1:5173"):
        with httpx.Client(base_url=base, timeout=10, trust_env=False) as client:
            health = client.get("/api/health")
            assert health.status_code == 200
            assert health.json() == {
                "status": "ok", "apiVersion": "1.0", "dataSource": "simulation"
            }
            checked += 1
            catalog = client.get("/api/v1/scenarios")
            assert catalog.status_code == 200
            assert [item["id"] for item in catalog.json()["scenarios"]] == list(SCENARIOS)
            checked += 1
            for scenario in SCENARIOS:
                response = client.get("/api/v1/snapshot", params={"scenario": scenario})
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("application/json")
                snapshot = response.json()
                VALIDATOR.validate(snapshot)
                expected = json.loads(
                    (ROOT / "contracts/examples" / f"{scenario}.json").read_text("utf-8")
                )
                assert snapshot == expected
                assert snapshot["ai"] == {"status": "not_connected", "explanation": None}
                assert len(snapshot["rooms"]) == 1
                if scenario == "stale-sensor":
                    assert snapshot["rooms"][0]["occupancy"] is None
                checked += 1
                print(f"PASS {base} {scenario}: schema and exact fixture parity")
            for method, path, status, code in (
                ("GET", "/api/v1/snapshot", 400, "INVALID_QUERY"),
                ("GET", "/api/v1/snapshot?scenario=unknown", 404, "UNKNOWN_SCENARIO"),
                (
                    "GET", "/api/v1/snapshot?scenario=idle-room&scenario=class-soon",
                    400, "INVALID_QUERY",
                ),
                ("GET", "/api/unknown", 404, "NOT_FOUND"),
                ("POST", "/api/health", 405, "METHOD_NOT_ALLOWED"),
            ):
                response = client.request(method, path)
                assert response.status_code == status
                assert response.json()["error"]["code"] == code
                if status == 405:
                    assert response.headers["allow"] == "GET"
                checked += 1
            print(f"PASS {base} health, catalog, and 400/404/405 compatibility")
    print(f"PASS {checked} real HTTP cases across backend and Vite proxy")


if __name__ == "__main__":
    verify()
