"""Load physical inputs from the frozen examples; ignore precomputed analysis/totals."""

import json
from decimal import Decimal
from pathlib import Path

from backend.app.models import ClassSchedule, EquipmentState, RoomState, SimulationState

SCENARIOS = (
    ("idle-room", "Idle room", "Fresh zero occupancy; AC and lights remain on."),
    ("occupied-room", "Occupied room", "An occupied classroom with a class in session."),
    ("class-soon", "Class soon", "An empty room with a class starting in 10 minutes."),
    ("stale-sensor", "Stale sensor", "Occupancy is unknown because its sensor is stale."),
)
SCENARIO_IDS = frozenset(item[0] for item in SCENARIOS)


class SimulationUnavailable(ValueError):
    """The approved source cannot supply safe, structured simulation inputs."""


def _object(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Expected a simulation object")
    return value


def _parse_room(source: object) -> RoomState:
    room = _object(source)
    devices = _object(room["devices"])
    return RoomState(
        room_id=room["roomId"],
        reported_occupancy=room["occupancy"],
        sensor_status=room["sensorStatus"],
        schedule=ClassSchedule(room["classInSession"], room["minutesToNextClass"]),
        equipment=EquipmentState(devices["acOn"], devices["lightsOn"]),
    )


def load_simulation(contracts_dir: Path, scenario_id: str) -> SimulationState:
    # Check before building a path; arbitrary scenario IDs never become filesystem paths.
    if scenario_id not in SCENARIO_IDS:
        raise ValueError("Unknown scenario ID")
    try:
        source = _object(
            json.loads(
                (contracts_dir / "examples" / f"{scenario_id}.json").read_text("utf-8"),
                parse_float=Decimal,
            )
        )
        if (
            source["apiVersion"] != "1.0"
            or source["scenarioId"] != scenario_id
            or source["dataSource"] != "simulation"
        ):
            raise ValueError("Simulation metadata does not match the frozen contract")
        if not isinstance(source["rooms"], list):
            raise ValueError("rooms must be an array")
        tariff = source["tariffMyrPerKwh"]
        # JSON integer tariffs are legal, but booleans and numeric strings are not.
        if type(tariff) is int:
            tariff = Decimal(tariff)
        return SimulationState(
            scenario_id=scenario_id,
            snapshot_at=source["snapshotAt"],
            analysis_window_minutes=source["analysisWindowMinutes"],
            tariff_myr_per_kwh=tariff,
            rooms=tuple(_parse_room(room) for room in source["rooms"]),
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SimulationUnavailable("Simulation inputs are unavailable") from exc
