"""Safety matrix across sensor trust, occupancy, and conflicting schedules."""

from dataclasses import replace

import pytest

from backend.app.analysis import analyze_simulation, build_snapshot
from backend.app.models import ClassSchedule, EquipmentState, RoomState
from backend.app.rules import ContractLimitation, recommend
from backend.app.schedule import ScheduleStatus, evaluate_schedule


def room(occupancy=0, sensor="fresh", *, active=False, minutes=120, ac=True, lights=True):
    return RoomState(
        "A101", occupancy, sensor, ClassSchedule(active, minutes), EquipmentState(ac, lights)
    )


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (0, ScheduleStatus.SOON),
        (14, ScheduleStatus.SOON),
        (15, ScheduleStatus.SOON),
        (16, ScheduleStatus.WINDOW_CONFLICT),
        (74, ScheduleStatus.WINDOW_CONFLICT),
        (75, ScheduleStatus.CLEAR),
        (120, ScheduleStatus.CLEAR),
        (None, ScheduleStatus.UNKNOWN),
    ],
)
def test_schedule_boundaries(minutes, expected):
    assert evaluate_schedule(ClassSchedule(False, minutes), 60, 15) == expected


@pytest.mark.parametrize("minutes", [0, 15, 75, None])
def test_active_class_takes_precedence_over_next_class(minutes):
    assert evaluate_schedule(ClassSchedule(True, minutes), 60, 15) == ScheduleStatus.ACTIVE


@pytest.mark.parametrize("sensor", ["fresh", "stale", "missing"])
@pytest.mark.parametrize("occupancy", [None, 0, 1, 24])
@pytest.mark.parametrize("schedule", [(False, 120), (False, 10), (True, 90), (False, None)])
def test_occupancy_sensor_and_schedule_safety_matrix(sensor, occupancy, schedule):
    active, minutes = schedule
    state = room(occupancy, sensor, active=active, minutes=minutes)
    if sensor == "fresh" and occupancy == 0 and (active or minutes is None):
        with pytest.raises(ContractLimitation):
            recommend(state, 60, 15)
        return
    decision = recommend(state, 60, 15)
    if sensor != "fresh" or occupancy is None:
        assert state.occupancy is None
        assert decision.status == "unknown"
        assert decision.code == "CHECK_SENSOR_DATA"
    elif occupancy > 0:
        assert decision.code == "NO_ACTION_OCCUPIED"
    elif minutes == 10:
        assert decision.code == "KEEP_ON_CLASS_SOON"
    else:
        assert decision.code == "REVIEW_IDLE_ROOM"
    if decision.code == "REVIEW_IDLE_ROOM":
        assert sensor == "fresh" and occupancy == 0 and not active
        assert minutes >= 75
        assert "human" in decision.rationale.lower()
    assert state.reported_occupancy == occupancy  # Inputs are never rewritten as controls.


@pytest.mark.parametrize("minutes", [0, 15])
def test_classes_starting_now_or_at_buffer_are_protected(minutes):
    decision = recommend(room(minutes=minutes), 60, 15)
    assert decision.code == "KEEP_ON_CLASS_SOON"
    assert decision.status == "normal"


@pytest.mark.parametrize("minutes", [16, 74, None])
def test_partial_or_unknown_window_is_a_contract_limitation(minutes):
    with pytest.raises(ContractLimitation):
        recommend(room(minutes=minutes), 60, 15)


def test_exact_clear_window_boundary_is_eligible_for_review():
    assert recommend(room(minutes=75), 60, 15).code == "REVIEW_IDLE_ROOM"


def test_all_off_empty_room_never_gets_a_fabricated_idle_review():
    with pytest.raises(ContractLimitation):
        recommend(room(ac=False, lights=False), 60, 15)


def test_longer_windows_are_protected_instead_of_claiming_partial_savings():
    with pytest.raises(ContractLimitation):
        recommend(room(minutes=75), 61, 15)


@pytest.mark.parametrize("sensor", ["stale", "missing"])
@pytest.mark.parametrize("reported_count", [0, 24])
def test_untrusted_counts_are_null_in_serialized_analysis(sensor, reported_count):
    from backend.app.main import CONTRACTS_DIR
    from backend.app.simulation import load_simulation

    state = load_simulation(CONTRACTS_DIR, "idle-room")
    state = replace(state, rooms=(room(reported_count, sensor),))
    report = analyze_simulation(state)
    snapshot = build_snapshot(report)
    assert snapshot["rooms"][0]["occupancy"] is None
    assert snapshot["rooms"][0]["analysis"]["recommendationCode"] == "CHECK_SENSOR_DATA"
    assert snapshot["summary"]["potentialSavingsKwh"] == 0
    assert snapshot["summary"]["roomsNeedingReview"] == 1
    assert report.rooms[0].energy.baseline_kwh > 0
