"""Conservative advisories using only the four frozen recommendation codes."""

from dataclasses import dataclass

from backend.app.models import AnalysisStatus, RecommendationCode, RoomState
from backend.app.schedule import ScheduleStatus, evaluate_schedule


class ContractLimitation(ValueError):
    """An input combination has no honest representation in the frozen contract."""


@dataclass(frozen=True)
class Recommendation:
    status: AnalysisStatus
    code: RecommendationCode
    rationale: str


def recommend(room: RoomState, window_minutes: int, buffer_minutes: int) -> Recommendation:
    if room.occupancy is None:
        return Recommendation(
            "unknown",
            "CHECK_SENSOR_DATA",
            "Occupancy is unknown or untrusted. Check sensor data; no savings are credited.",
        )
    if room.occupancy > 0:
        return Recommendation(
            "normal",
            "NO_ACTION_OCCUPIED",
            "Fresh occupancy confirms people are present. Retain the current equipment state.",
        )
    schedule = evaluate_schedule(room.schedule, window_minutes, buffer_minutes)
    if schedule == ScheduleStatus.SOON:
        return Recommendation(
            "normal",
            "KEEP_ON_CLASS_SOON",
            "A class starts within the preconditioning buffer. Retain the current state.",
        )
    if schedule != ScheduleStatus.CLEAR:
        raise ContractLimitation(
            f"Empty room with schedule {schedule.value} has no approved recommendation code"
        )
    if not (room.equipment.ac_on or room.equipment.lights_on):
        raise ContractLimitation("Empty room with all equipment off has no approved idle code")
    return Recommendation(
        "review",
        "REVIEW_IDLE_ROOM",
        "Fresh zero occupancy and a clear full window indicate possible waste. "
        "A human may review switching off enabled devices; savings are simulated estimates only.",
    )
