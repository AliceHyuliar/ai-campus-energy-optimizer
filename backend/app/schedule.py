"""Evaluate relative simulation schedules without consulting the system clock."""

from enum import Enum

from backend.app.models import ClassSchedule, require_integer


class ScheduleStatus(Enum):
    ACTIVE = "active"
    SOON = "soon"
    CLEAR = "clear"
    UNKNOWN = "unknown"
    WINDOW_CONFLICT = "window_conflict"


def evaluate_schedule(
    schedule: ClassSchedule, window_minutes: int, buffer_minutes: int
) -> ScheduleStatus:
    require_integer("window_minutes", window_minutes, 1, 1440)
    require_integer("buffer_minutes", buffer_minutes, 0)
    if schedule.class_in_session:
        return ScheduleStatus.ACTIVE
    minutes = schedule.minutes_to_next_class
    if minutes is None:
        return ScheduleStatus.UNKNOWN
    if minutes <= buffer_minutes:
        return ScheduleStatus.SOON
    if minutes >= window_minutes + buffer_minutes:
        return ScheduleStatus.CLEAR
    return ScheduleStatus.WINDOW_CONFLICT
