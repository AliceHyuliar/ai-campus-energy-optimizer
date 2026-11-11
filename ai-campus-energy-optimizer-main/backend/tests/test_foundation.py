"""Contract and HTTP regression checks for the common foundation."""

import json
from decimal import ROUND_HALF_UP, Decimal

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.main import CONTRACTS_DIR, SCENARIO_IDS, app

SCHEMA = json.loads((CONTRACTS_DIR / "snapshot.schema.json").read_text("utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
client = TestClient(app)


def fixture(scenario: str) -> dict:
    return json.loads((CONTRACTS_DIR / "examples" / f"{scenario}.json").read_text("utf-8"))


def test_schema_and_fixture_inventory():
    Draft202012Validator.check_schema(SCHEMA)
    assert {path.stem for path in (CONTRACTS_DIR / "examples").glob("*.json")} == SCENARIO_IDS


@pytest.mark.parametrize("scenario", sorted(SCENARIO_IDS))
def test_examples_match_schema_and_summary(scenario):
    data = fixture(scenario)
    VALIDATOR.validate(data)
    assert data["scenarioId"] == scenario
    rooms = data["rooms"]
    summary = data["summary"]
    assert len({room["roomId"] for room in rooms}) == len(rooms)
    assert summary["roomsMonitored"] == len(rooms)
    assert summary["roomsNeedingReview"] == sum(
        room["analysis"]["status"] in {"review", "unknown"} for room in rooms
    )
    energy = sum(Decimal(str(room["analysis"]["potentialSavingsKwh"])) for room in rooms)
    assert Decimal(str(summary["potentialSavingsKwh"])) == energy
    expected_cost = (energy * Decimal(str(data["tariffMyrPerKwh"]))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert Decimal(str(summary["potentialSavingsMyr"])) == expected_cost
    for room in rooms:
        estimate = Decimal(str(room["analysis"]["potentialSavingsKwh"]))
        assert estimate == estimate.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        if room["analysis"]["status"] == "review":
            assert room["minutesToNextClass"] >= data["analysisWindowMinutes"] + 15


def test_estimate_matches_documented_assumptions():
    data = fixture("idle-room")
    expected = (Decimal("2.0") + Decimal("0.2")) * data["analysisWindowMinutes"] / 60
    assert Decimal(str(data["summary"]["potentialSavingsKwh"])) == expected


def test_non_idle_examples_do_not_claim_savings():
    for scenario in SCENARIO_IDS - {"idle-room"}:
        assert fixture(scenario)["summary"]["potentialSavingsKwh"] == 0
    stale = fixture("stale-sensor")["rooms"][0]
    assert stale["occupancy"] is None
    assert stale["analysis"]["status"] == "unknown"


@pytest.mark.parametrize("mutation", ["zero-stale", "null-fresh-review", "missing-occupancy"])
def test_unknown_occupancy_cannot_become_an_idle_recommendation(mutation):
    data = fixture("idle-room")
    room = data["rooms"][0]
    if mutation == "zero-stale":
        room["sensorStatus"] = "stale"
    elif mutation == "null-fresh-review":
        room["occupancy"] = None
    else:
        del room["occupancy"]
    assert not VALIDATOR.is_valid(data)


def test_health_and_scenario_catalog():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "apiVersion": "1.0", "dataSource": "simulation"}
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()["scenarios"]} == SCENARIO_IDS


@pytest.mark.parametrize("scenario", sorted(SCENARIO_IDS))
def test_http_snapshot_matches_shared_fixture(scenario):
    response = client.get("/api/v1/snapshot", params={"scenario": scenario})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == fixture(scenario)
    VALIDATOR.validate(response.json())


@pytest.mark.parametrize(
    "query",
    ["", "?scenario=", "?scenario=%20", "?scenario=idle-room&scenario=class-soon"],
)
def test_invalid_query(query):
    response = client.get(f"/api/v1/snapshot{query}")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_QUERY"


@pytest.mark.parametrize("scenario", ["unknown", "../idle-room", "IDLE-ROOM"])
def test_unknown_scenario(scenario):
    response = client.get("/api/v1/snapshot", params={"scenario": scenario})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "UNKNOWN_SCENARIO"


def test_unknown_route_and_method():
    assert client.get("/api/nope").json()["error"]["code"] == "NOT_FOUND"
    response = client.post("/api/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_missing_fixture_is_a_structured_error(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.app.main.CONTRACTS_DIR", tmp_path)
    response = client.get("/api/v1/snapshot?scenario=idle-room")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "FIXTURE_UNAVAILABLE"
