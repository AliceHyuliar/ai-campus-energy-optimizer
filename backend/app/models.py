"""Immutable simulation inputs. All values describe synthetic state, never controls."""

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

SensorStatus = Literal["fresh", "stale", "missing"]
AnalysisStatus = Literal["review", "normal", "unknown"]
RecommendationCode = Literal[
    "REVIEW_IDLE_ROOM", "NO_ACTION_OCCUPIED", "KEEP_ON_CLASS_SOON", "CHECK_SENSOR_DATA"
]


def require_integer(name: str, value: int, minimum: int, maximum: int | None = None) -> None:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be an integer in the supported range")


def require_decimal(name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError(f"{name} must be a finite nonnegative Decimal")


@dataclass(frozen=True)
class EquipmentState:
    ac_on: bool
    lights_on: bool

    def __post_init__(self) -> None:
        if type(self.ac_on) is not bool or type(self.lights_on) is not bool:
            raise ValueError("Equipment states must be booleans")


@dataclass(frozen=True)
class ClassSchedule:
    class_in_session: bool
    minutes_to_next_class: int | None

    def __post_init__(self) -> None:
        if type(self.class_in_session) is not bool:
            raise ValueError("class_in_session must be boolean")
        if self.minutes_to_next_class is not None:
            require_integer("minutes_to_next_class", self.minutes_to_next_class, 0)


@dataclass(frozen=True)
class RoomState:
    room_id: str
    reported_occupancy: int | None
    sensor_status: SensorStatus
    schedule: ClassSchedule
    equipment: EquipmentState

    def __post_init__(self) -> None:
        if not isinstance(self.room_id, str) or not 1 <= len(self.room_id) <= 64:
            raise ValueError("room_id must contain 1 to 64 characters")
        if self.reported_occupancy is not None:
            require_integer("reported_occupancy", self.reported_occupancy, 0)
        if self.sensor_status not in ("fresh", "stale", "missing"):
            raise ValueError("Unsupported sensor status")
        if not isinstance(self.schedule, ClassSchedule):
            raise ValueError("A structured class schedule is required")
        if not isinstance(self.equipment, EquipmentState):
            raise ValueError("Structured equipment state is required")

    @property
    def occupancy(self) -> int | None:
        """Only fresh counts are trusted; stale/missing counts remain unknown."""
        return self.reported_occupancy if self.sensor_status == "fresh" else None


@dataclass(frozen=True)
class EnergyAssumptions:
    ac_power_kw: Decimal = Decimal("2.0")
    lighting_power_kw: Decimal = Decimal("0.2")
    preconditioning_minutes: int = 15

    def __post_init__(self) -> None:
        require_decimal("ac_power_kw", self.ac_power_kw)
        require_decimal("lighting_power_kw", self.lighting_power_kw)
        # The frozen KEEP_ON_CLASS_SOON code is defined as 0–15 minutes inclusive.
        require_integer("preconditioning_minutes", self.preconditioning_minutes, 15, 15)


DEFAULT_ASSUMPTIONS = EnergyAssumptions()


@dataclass(frozen=True)
class SimulationState:
    scenario_id: str
    snapshot_at: str
    analysis_window_minutes: int
    tariff_myr_per_kwh: Decimal
    rooms: tuple[RoomState, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_id, str) or not self.scenario_id:
            raise ValueError("A scenario ID is required")
        if not isinstance(self.snapshot_at, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", self.snapshot_at
        ):
            raise ValueError("snapshot_at must use UTC seconds with a Z suffix")
        datetime.strptime(self.snapshot_at, "%Y-%m-%dT%H:%M:%SZ")
        require_integer("analysis_window_minutes", self.analysis_window_minutes, 1, 1440)
        require_decimal("tariff_myr_per_kwh", self.tariff_myr_per_kwh)
        if not isinstance(self.rooms, tuple) or len(self.rooms) != 1:
            raise ValueError("The approved MVP supports exactly one classroom per scenario")
        if not isinstance(self.rooms[0], RoomState):
            raise ValueError("A structured room is required")
