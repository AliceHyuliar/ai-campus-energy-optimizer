"""Multi-classroom acceptance tests and original-scenario regression protection."""

import hashlib
import json
from dataclasses import replace
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.analysis import analyze_simulation, build_snapshot
from backend.app.main import CONTRACTS_DIR, app
from backend.app.models import ClassSchedule, EquipmentState
from backend.app.simulation import SCENARIO_IDS, load_simulation

client = TestClient(app)
validator = Draft202012Validator(
    json.loads((CONTRACTS_DIR / "snapshot.schema.json").read_text("utf-8")),
    format_checker=FormatChecker(),
)
ORIGINAL_FIXTURES = {
    "idle-room": "e37e4feb50f25353d9ae38194e322c6fe61c5545b9fdc6c552d692aef7d8c331",
    "occupied-room": "ec9e716a6a74a004e7083684d16ec109d2706c44349c11545d65f286408a1962",
    "class-soon": "ee350417df36280bec00e73673151350c38066082cbb6bfa728954b775d9d7b9",
    "stale-sensor": "16fe8f5ff527069f303e562e881820973eb3e975b11fa739f56f3a6c7bf26646",
}
ORDERED_IDS = [*ORIGINAL_FIXTURES, "campus-overview"]


def campus():
    return load_simulation(CONTRACTS_DIR, "campus-overview")


def snapshot(state):
    result = build_snapshot(analyze_simulation(state))
    validator.validate(result)
    return result


def publish_input(tmp_path, monkeypatch, source):
    directory = tmp_path / "examples"
    directory.mkdir()
    (directory / "campus-overview.json").write_text(json.dumps(source), encoding="utf-8")
    monkeypatch.setattr("backend.app.main.CONTRACTS_DIR", tmp_path)


def campus_source():
    return json.loads((CONTRACTS_DIR / "examples/campus-overview.json").read_text("utf-8"))


def assert_unavailable(response):
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "FIXTURE_UNAVAILABLE", "message": "Simulation fixture is unavailable."}
    }


@pytest.mark.parametrize("scenario", ORIGINAL_FIXTURES)
def test_original_fixtures_and_api_outputs_are_unchanged(scenario):
    raw = (CONTRACTS_DIR / "examples" / f"{scenario}.json").read_bytes()
    # Ignore platform checkout line endings, but freeze every original JSON value/content.
    assert hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == ORIGINAL_FIXTURES[scenario]
    response = client.get("/api/v1/snapshot", params={"scenario": scenario})
    assert response.status_code == 200
    assert response.json() == json.loads(raw)


def test_catalog_appends_fifth_scenario_and_preserves_existing_entries():
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    entries = response.json()["scenarios"]
    assert [entry["id"] for entry in entries] == ORDERED_IDS
    assert SCENARIO_IDS == set(ORDERED_IDS)
    assert entries[:4] == [
        {
            "id": "idle-room",
            "name": "Idle room",
            "description": "Fresh zero occupancy; AC and lights remain on.",
        },
        {
            "id": "occupied-room",
            "name": "Occupied room",
            "description": "An occupied classroom with a class in session.",
        },
        {
            "id": "class-soon",
            "name": "Class soon",
            "description": "An empty room with a class starting in 10 minutes.",
        },
        {
            "id": "stale-sensor",
            "name": "Stale sensor",
            "description": "Occupancy is unknown because its sensor is stale.",
        },
    ]
    assert entries[4] == {
        "id": "campus-overview",
        "name": "Campus overview",
        "description": (
            "Four simulated classrooms with idle, occupied, class-soon, and stale-sensor states."
        ),
    }
    assert response.json()["apiVersion"] == "1.0"


def test_campus_room_states_and_summary_match_approved_requirements():
    result = snapshot(campus())
    expected = [
        ("A101", 0, "fresh", False, 120, "review", "REVIEW_IDLE_ROOM", 2.2),
        ("A102", 24, "fresh", True, 90, "normal", "NO_ACTION_OCCUPIED", 0),
        ("A103", 0, "fresh", False, 10, "normal", "KEEP_ON_CLASS_SOON", 0),
        ("A104", None, "stale", False, None, "unknown", "CHECK_SENSOR_DATA", 0),
    ]
    for room, values in zip(result["rooms"], expected, strict=True):
        room_id, occupancy, sensor, active, minutes, status, code, energy = values
        assert room == {
            "roomId": room_id,
            "occupancy": occupancy,
            "sensorStatus": sensor,
            "classInSession": active,
            "minutesToNextClass": minutes,
            "devices": {"acOn": True, "lightsOn": True},
            "analysis": {
                "status": status,
                "recommendationCode": code,
                "potentialSavingsKwh": energy,
            },
        }
    assert result["summary"] == {
        "roomsMonitored": 4,
        "roomsNeedingReview": 2,
        "potentialSavingsKwh": 2.2,
        "potentialSavingsMyr": 1.1,
    }
    assert result["snapshotAt"] == "2026-11-09T00:00:00Z"
    assert result["analysisWindowMinutes"] == 60
    assert result["tariffMyrPerKwh"] == 0.5
    assert result["dataSource"] == "simulation"
    assert result["ai"] == {"status": "not_connected", "explanation": None}


@pytest.mark.parametrize("count", [1, 2, 4, 5])
def test_model_accepts_one_or_more_unique_classrooms(count):
    state = campus()
    rooms = tuple(replace(state.rooms[0], room_id=f"R{index}") for index in range(count))
    result = snapshot(replace(state, rooms=rooms))
    assert len(result["rooms"]) == count
    assert result["summary"]["roomsMonitored"] == count
    assert result["summary"]["roomsNeedingReview"] == count
    assert Decimal(str(result["summary"]["potentialSavingsKwh"])) == Decimal("2.2") * count


@pytest.mark.parametrize("collection", [(), [], None, "rooms", {}])
def test_model_rejects_empty_or_unstructured_collections(collection):
    with pytest.raises(ValueError, match="nonempty tuple"):
        replace(campus(), rooms=collection)


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("invalid", [None, {}, "room"])
def test_model_validates_every_room_not_only_the_first(position, invalid):
    state = campus()
    rooms = list(state.rooms)
    rooms[position] = invalid
    with pytest.raises(ValueError, match="Every classroom"):
        replace(state, rooms=tuple(rooms))


@pytest.mark.parametrize("position", [1, 2, 3])
def test_duplicate_ids_are_rejected_even_when_room_contents_differ(position):
    state = campus()
    rooms = list(state.rooms)
    rooms[position] = replace(rooms[position], room_id="A101")
    with pytest.raises(ValueError, match="unique"):
        replace(state, rooms=tuple(rooms))


@pytest.mark.parametrize("position", range(4))
def test_room_decisions_and_totals_are_independent(position):
    state = campus()
    original = snapshot(state)
    changes = [
        {"reported_occupancy": 1},
        {
            "reported_occupancy": 0,
            "schedule": ClassSchedule(False, 120),
            "equipment": EquipmentState(False, True),
        },
        {"schedule": ClassSchedule(False, 75)},
        {"reported_occupancy": 0, "sensor_status": "fresh", "schedule": ClassSchedule(False, 120)},
    ]
    expected = [
        ("NO_ACTION_OCCUPIED", 0, 0, 1),
        ("REVIEW_IDLE_ROOM", 2.4, 1.2, 3),
        ("REVIEW_IDLE_ROOM", 4.4, 2.2, 3),
        ("REVIEW_IDLE_ROOM", 4.4, 2.2, 2),
    ]
    rooms = list(state.rooms)
    rooms[position] = replace(rooms[position], **changes[position])
    result = snapshot(replace(state, rooms=tuple(rooms)))
    code, energy, cost, review_count = expected[position]
    assert result["rooms"][position]["analysis"]["recommendationCode"] == code
    assert result["summary"] == {
        "roomsMonitored": 4,
        "roomsNeedingReview": review_count,
        "potentialSavingsKwh": energy,
        "potentialSavingsMyr": cost,
    }
    for index in range(4):
        if index != position:
            assert result["rooms"][index] == original["rooms"][index]
    assert snapshot(state) == original  # Analysis never mutates the input scenario.


def test_reordering_rooms_preserves_per_id_decisions_and_totals():
    state = campus()
    original = snapshot(state)
    reordered = snapshot(replace(state, rooms=tuple(reversed(state.rooms))))
    assert reordered["summary"] == original["summary"]
    assert reordered["rooms"] == list(reversed(original["rooms"]))


@pytest.mark.parametrize(
    ("minutes", "ac", "per_room", "total", "money", "individual_cost_sum"),
    [(1, False, "0.003", "0.012", "0.01", "0.00"), (3, True, "0.110", "0.440", "0.22", "0.24")],
)
def test_aggregation_rounds_emitted_energy_then_total_money(
    minutes, ac, per_room, total, money, individual_cost_sum
):
    state = campus()
    rooms = tuple(
        replace(state.rooms[0], room_id=f"R{index}", equipment=EquipmentState(ac, True))
        for index in range(4)
    )
    report = analyze_simulation(replace(state, rooms=rooms, analysis_window_minutes=minutes))
    result = build_snapshot(report)
    validator.validate(result)
    assert all(item.energy.potential_savings_kwh == Decimal(per_room) for item in report.rooms)
    assert report.potential_savings_kwh == Decimal(total)
    assert Decimal(str(result["summary"]["potentialSavingsMyr"])) == Decimal(money)
    assert sum(item.energy.potential_savings_myr for item in report.rooms) == Decimal(
        individual_cost_sum
    )


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("sensor", ["fresh", "stale", "missing"])
def test_unknown_or_untrusted_occupancy_never_earns_savings_in_any_position(position, sensor):
    state = campus()
    original = snapshot(state)
    rooms = list(state.rooms)
    reported = None if sensor == "fresh" else 0
    rooms[position] = replace(rooms[position], reported_occupancy=reported, sensor_status=sensor)
    result = snapshot(replace(state, rooms=tuple(rooms)))
    changed = result["rooms"][position]
    assert changed["occupancy"] is None
    assert changed["analysis"] == {
        "status": "unknown",
        "recommendationCode": "CHECK_SENSOR_DATA",
        "potentialSavingsKwh": 0,
    }
    assert result["summary"]["potentialSavingsKwh"] == (0 if position == 0 else 2.2)
    for index in range(4):
        if index != position:
            assert result["rooms"][index] == original["rooms"][index]


@pytest.mark.parametrize("state_kind", ["occupied", "unknown"])
def test_all_protected_rooms_have_positive_consumption_but_zero_savings(state_kind):
    state = campus()
    rooms = tuple(
        replace(
            room,
            reported_occupancy=24 if state_kind == "occupied" else 0,
            sensor_status="fresh" if state_kind == "occupied" else "missing",
        )
        for room in state.rooms
    )
    report = analyze_simulation(replace(state, rooms=rooms))
    result = build_snapshot(report)
    assert all(item.energy.baseline_kwh == Decimal("2.200") for item in report.rooms)
    assert result["summary"] == {
        "roomsMonitored": 4,
        "roomsNeedingReview": 4 if state_kind == "unknown" else 0,
        "potentialSavingsKwh": 0,
        "potentialSavingsMyr": 0,
    }
    validator.validate(result)


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("problem", ["active", "unknown-time", "partial-window", "all-off"])
def test_one_unsupported_room_fails_the_entire_http_snapshot(
    tmp_path, monkeypatch, position, problem
):
    source = campus_source()
    room = source["rooms"][position]
    room.update(occupancy=0, sensorStatus="fresh", classInSession=False, minutesToNextClass=120)
    if problem == "active":
        room["classInSession"] = True
    elif problem == "unknown-time":
        room["minutesToNextClass"] = None
    elif problem == "partial-window":
        room["minutesToNextClass"] = 16
    else:
        room["devices"] = {"acOn": False, "lightsOn": False}
    publish_input(tmp_path, monkeypatch, source)
    assert_unavailable(client.get("/api/v1/snapshot?scenario=campus-overview"))


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("problem", ["missing-count", "negative-count", "invalid-device"])
def test_one_malformed_room_fails_the_entire_http_snapshot(
    tmp_path, monkeypatch, position, problem
):
    source = campus_source()
    room = source["rooms"][position]
    if problem == "missing-count":
        del room["occupancy"]
    elif problem == "negative-count":
        room["occupancy"] = -1
    else:
        room["devices"]["acOn"] = "true"
    publish_input(tmp_path, monkeypatch, source)
    assert_unavailable(client.get("/api/v1/snapshot?scenario=campus-overview"))


@pytest.mark.parametrize("problem", ["empty", "duplicate", "not-array"])
def test_invalid_room_collections_preserve_http_error_envelope(tmp_path, monkeypatch, problem):
    source = campus_source()
    if problem == "empty":
        source["rooms"] = []
    elif problem == "duplicate":
        source["rooms"][3]["roomId"] = "A101"
    else:
        source["rooms"] = {"A101": source["rooms"][0]}
    publish_input(tmp_path, monkeypatch, source)
    assert_unavailable(client.get("/api/v1/snapshot?scenario=campus-overview"))


def test_campus_results_are_recomputed_instead_of_echoing_authored_analyses(tmp_path, monkeypatch):
    source = campus_source()
    source["summary"] = {"potentialSavingsKwh": 999}
    source["ai"] = {"status": "fake", "explanation": "fake"}
    for room in source["rooms"]:
        room["analysis"] = {"status": "review", "potentialSavingsKwh": 999}
    publish_input(tmp_path, monkeypatch, source)
    response = client.get("/api/v1/snapshot?scenario=campus-overview")
    assert response.status_code == 200
    assert response.json() == campus_source()
