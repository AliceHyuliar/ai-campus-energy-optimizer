"""Generated outputs, input validation, API compatibility, and AI isolation."""

import json
from dataclasses import FrozenInstanceError, replace
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.ai import ExplanationProvider, disconnected_ai
from backend.app.analysis import analyze_simulation, build_snapshot
from backend.app.main import CONTRACTS_DIR, app
from backend.app.models import ClassSchedule, EquipmentState, RoomState
from backend.app.simulation import SCENARIO_IDS, SCENARIOS, SimulationUnavailable, load_simulation

client = TestClient(app)
validator = Draft202012Validator(
    json.loads((CONTRACTS_DIR / "snapshot.schema.json").read_text("utf-8")),
    format_checker=FormatChecker(),
)


def example(scenario="idle-room"):
    return json.loads((CONTRACTS_DIR / "examples" / f"{scenario}.json").read_text("utf-8"))


def write_input(tmp_path, data):
    directory = tmp_path / "examples"
    directory.mkdir(exist_ok=True)
    (directory / "idle-room.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize("scenario", sorted(SCENARIO_IDS))
def test_generated_snapshot_has_exact_fixture_parity_and_valid_schema(scenario):
    report = analyze_simulation(load_simulation(CONTRACTS_DIR, scenario))
    snapshot = build_snapshot(report)
    assert snapshot == example(scenario)
    validator.validate(snapshot)
    expected_count = 4 if scenario == "campus-overview" else 1
    assert len(report.rooms) == len(snapshot["rooms"]) == expected_count
    assert all(room.energy.baseline_kwh == Decimal("2.200") for room in report.rooms)
    assert snapshot["summary"]["potentialSavingsKwh"] == sum(
        room["analysis"]["potentialSavingsKwh"] for room in snapshot["rooms"]
    )
    expected_cost = (report.potential_savings_kwh * report.simulation.tariff_myr_per_kwh).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert snapshot["summary"]["potentialSavingsMyr"] == float(expected_cost)


def test_generated_analysis_does_not_echo_precomputed_fixture_results(tmp_path):
    source = example()
    source["summary"] = {"potentialSavingsKwh": 99999}
    source["rooms"][0]["analysis"] = {"status": "unknown", "potentialSavingsKwh": 99999}
    source["ai"] = {"status": "invented-provider", "explanation": "untrusted text"}
    write_input(tmp_path, source)
    assert build_snapshot(analyze_simulation(load_simulation(tmp_path, "idle-room"))) == example()


def test_calculation_uses_equipment_inputs_instead_of_scenario_name(tmp_path, monkeypatch):
    source = example()
    source["rooms"][0]["devices"]["acOn"] = False
    write_input(tmp_path, source)
    monkeypatch.setattr("backend.app.main.CONTRACTS_DIR", tmp_path)
    response = client.get("/api/v1/snapshot?scenario=idle-room")
    assert response.status_code == 200
    snapshot = response.json()
    validator.validate(snapshot)
    assert snapshot["summary"]["potentialSavingsKwh"] == 0.2
    assert snapshot["summary"]["potentialSavingsMyr"] == 0.1


@pytest.mark.parametrize("count", [None, 1])
def test_rule_uses_occupancy_inputs_instead_of_scenario_name(tmp_path, count):
    source = example()
    source["rooms"][0]["occupancy"] = count
    write_input(tmp_path, source)
    snapshot = build_snapshot(analyze_simulation(load_simulation(tmp_path, "idle-room")))
    validator.validate(snapshot)
    assert snapshot["summary"]["potentialSavingsKwh"] == 0
    assert snapshot["rooms"][0]["analysis"]["status"] == ("unknown" if count is None else "normal")


def test_rounding_and_summary_use_emitted_energy():
    state = replace(load_simulation(CONTRACTS_DIR, "idle-room"), analysis_window_minutes=1)
    snapshot = build_snapshot(analyze_simulation(state))
    validator.validate(snapshot)
    assert snapshot["summary"]["potentialSavingsKwh"] == 0.037
    assert snapshot["summary"]["potentialSavingsMyr"] == 0.02


@pytest.mark.parametrize("field", ["occupancy", "sensorStatus", "minutesToNextClass", "devices"])
def test_missing_room_inputs_fail_without_unsafe_defaults(tmp_path, field):
    source = example()
    del source["rooms"][0][field]
    write_input(tmp_path, source)
    with pytest.raises(SimulationUnavailable):
        load_simulation(tmp_path, "idle-room")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("occupancy", -1),
        ("occupancy", True),
        ("occupancy", "0"),
        ("sensorStatus", "live"),
        ("classInSession", 0),
        ("minutesToNextClass", -1),
    ],
)
def test_invalid_room_inputs_fail(tmp_path, field, value):
    source = example()
    source["rooms"][0][field] = value
    write_input(tmp_path, source)
    with pytest.raises(SimulationUnavailable):
        load_simulation(tmp_path, "idle-room")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("snapshotAt", "2026-02-30T00:00:00Z"),
        ("snapshotAt", "2026-11-09T08:00:00+08:00"),
        ("analysisWindowMinutes", 0),
        ("analysisWindowMinutes", True),
        ("tariffMyrPerKwh", "0.5"),
        ("tariffMyrPerKwh", -0.5),
        ("tariffMyrPerKwh", True),
        ("tariffMyrPerKwh", float("nan")),
        ("scenarioId", "class-soon"),
        ("dataSource", "real"),
        ("apiVersion", "2.0"),
    ],
)
def test_invalid_metadata_fails(tmp_path, field, value):
    source = example()
    source[field] = value
    write_input(tmp_path, source)
    with pytest.raises(SimulationUnavailable):
        load_simulation(tmp_path, "idle-room")


@pytest.mark.parametrize("room_count", [0, 2, 4])
def test_data_layer_rejects_empty_or_duplicate_classrooms(tmp_path, room_count):
    source = example()
    source["rooms"] *= room_count
    write_input(tmp_path, source)
    with pytest.raises(SimulationUnavailable):
        load_simulation(tmp_path, "idle-room")


@pytest.mark.parametrize("contents", ["{", "[]", "null", '{"rooms": null}'])
def test_unreadable_input_preserves_exact_http_error(tmp_path, monkeypatch, contents):
    directory = tmp_path / "examples"
    directory.mkdir()
    (directory / "idle-room.json").write_text(contents, encoding="utf-8")
    monkeypatch.setattr("backend.app.main.CONTRACTS_DIR", tmp_path)
    response = client.get("/api/v1/snapshot?scenario=idle-room")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "FIXTURE_UNAVAILABLE", "message": "Simulation fixture is unavailable."}
    }


def test_unsupported_schedule_fails_closed_with_existing_http_error(tmp_path, monkeypatch):
    source = example()
    source["rooms"][0]["minutesToNextClass"] = 16
    write_input(tmp_path, source)
    monkeypatch.setattr("backend.app.main.CONTRACTS_DIR", tmp_path)
    response = client.get("/api/v1/snapshot?scenario=idle-room")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "FIXTURE_UNAVAILABLE"


@pytest.mark.parametrize("scenario", ["../idle-room", "", "IDLE-ROOM", " idle-room "])
def test_loader_rejects_unknown_ids_before_file_access(tmp_path, monkeypatch, scenario):
    def unexpected_read(*args, **kwargs):
        pytest.fail("Unknown scenario must not cause a file read")

    monkeypatch.setattr(type(tmp_path), "read_text", unexpected_read)
    with pytest.raises(ValueError, match="Unknown scenario"):
        load_simulation(tmp_path, scenario)


def test_catalog_order_fields_and_messages_are_unchanged():
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    assert response.json() == {
        "apiVersion": "1.0",
        "dataSource": "simulation",
        "scenarios": [
            {"id": key, "name": name, "description": description}
            for key, name, description in SCENARIOS
        ],
    }
    invalid = client.get("/api/v1/snapshot?scenario=idle-room&scenario=")
    assert invalid.status_code == 400
    assert invalid.json() == {
        "error": {
            "code": "INVALID_QUERY",
            "message": "Provide exactly one non-empty scenario parameter.",
        }
    }
    unknown = client.get("/api/v1/snapshot?scenario=%20idle-room%20")
    assert unknown.status_code == 404
    assert unknown.json() == {
        "error": {"code": "UNKNOWN_SCENARIO", "message": "Unknown scenario. See /api/v1/scenarios."}
    }
    assert client.post("/api/health").headers["allow"] == "GET"
    assert client.get("/api/v1/snapshot?scenario=idle-room&extra=ignored").json() == example()


def test_input_and_reports_are_immutable_and_response_mutation_cannot_leak():
    state = load_simulation(CONTRACTS_DIR, "idle-room")
    report = analyze_simulation(state)
    with pytest.raises(FrozenInstanceError):
        state.rooms[0].reported_occupancy = 100
    with pytest.raises(FrozenInstanceError):
        report.rooms[0].recommendation.code = "NO_ACTION_OCCUPIED"
    first = build_snapshot(report)
    first["rooms"][0]["devices"]["acOn"] = False
    first["ai"]["status"] = "fake"
    assert build_snapshot(report) == example()
    assert client.get("/api/v1/snapshot?scenario=idle-room").json() == example()


def test_sensor_freshness_and_fixture_time_never_use_wall_clock(monkeypatch):
    class NoClock(datetime):
        @classmethod
        def now(cls, *args, **kwargs):
            pytest.fail("Simulation must not read current time")

        @classmethod
        def utcnow(cls):
            pytest.fail("Simulation must not read current time")

    monkeypatch.setattr("backend.app.models.datetime", NoClock)
    for scenario in SCENARIO_IDS:
        assert build_snapshot(analyze_simulation(load_simulation(CONTRACTS_DIR, scenario))) == (
            example(scenario)
        )


def test_ai_interface_is_provider_independent_and_never_called(monkeypatch):
    def unexpected_call(*args, **kwargs):
        pytest.fail("No explanation provider may be invoked while access is pending")

    monkeypatch.setattr(ExplanationProvider, "explain", unexpected_call)
    assert disconnected_ai() == {"status": "not_connected", "explanation": None}
    report = analyze_simulation(load_simulation(CONTRACTS_DIR, "idle-room"))
    assert report.assumptions.ac_power_kw == Decimal("2.0")
    assert report.rooms[0].recommendation.rationale
    assert build_snapshot(report)["ai"] == {"status": "not_connected", "explanation": None}


@pytest.mark.parametrize("invalid", [True, -1, 0.5, "0"])
def test_direct_model_construction_rejects_invalid_occupancy(invalid):
    with pytest.raises(ValueError):
        RoomState("A101", invalid, "fresh", ClassSchedule(False, 120), EquipmentState(True, True))
