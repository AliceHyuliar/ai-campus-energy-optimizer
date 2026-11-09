"""Compose pure analysis and serialize only fields approved by the frozen contract."""

from dataclasses import dataclass
from decimal import Decimal

from backend.app.ai import disconnected_ai
from backend.app.energy import EnergyEstimate, cost_myr, estimate_energy
from backend.app.models import DEFAULT_ASSUMPTIONS, EnergyAssumptions, RoomState, SimulationState
from backend.app.rules import Recommendation, recommend


@dataclass(frozen=True)
class RoomAnalysis:
    room: RoomState
    recommendation: Recommendation
    energy: EnergyEstimate


@dataclass(frozen=True)
class AnalysisReport:
    simulation: SimulationState
    assumptions: EnergyAssumptions
    rooms: tuple[RoomAnalysis, ...]

    @property
    def potential_savings_kwh(self) -> Decimal:
        return sum((room.energy.potential_savings_kwh for room in self.rooms), Decimal(0))


def analyze_simulation(
    simulation: SimulationState, assumptions: EnergyAssumptions = DEFAULT_ASSUMPTIONS
) -> AnalysisReport:
    analyses = []
    for room in simulation.rooms:
        decision = recommend(
            room, simulation.analysis_window_minutes, assumptions.preconditioning_minutes
        )
        energy = estimate_energy(
            room.equipment,
            simulation.analysis_window_minutes,
            simulation.tariff_myr_per_kwh,
            assumptions,
            eligible_for_savings=decision.code == "REVIEW_IDLE_ROOM",
        )
        analyses.append(RoomAnalysis(room, decision, energy))
    return AnalysisReport(simulation, assumptions, tuple(analyses))


def build_snapshot(report: AnalysisReport) -> dict:
    simulation = report.simulation
    return {
        "apiVersion": "1.0",
        "scenarioId": simulation.scenario_id,
        "dataSource": "simulation",
        "snapshotAt": simulation.snapshot_at,
        "analysisWindowMinutes": simulation.analysis_window_minutes,
        "tariffMyrPerKwh": float(simulation.tariff_myr_per_kwh),
        "summary": {
            "roomsMonitored": len(report.rooms),
            "roomsNeedingReview": sum(
                room.recommendation.status in ("review", "unknown") for room in report.rooms
            ),
            "potentialSavingsKwh": float(report.potential_savings_kwh),
            "potentialSavingsMyr": float(
                cost_myr(report.potential_savings_kwh, simulation.tariff_myr_per_kwh)
            ),
        },
        "rooms": [
            {
                "roomId": item.room.room_id,
                "occupancy": item.room.occupancy,
                "sensorStatus": item.room.sensor_status,
                "classInSession": item.room.schedule.class_in_session,
                "minutesToNextClass": item.room.schedule.minutes_to_next_class,
                "devices": {
                    "acOn": item.room.equipment.ac_on,
                    "lightsOn": item.room.equipment.lights_on,
                },
                "analysis": {
                    "status": item.recommendation.status,
                    "recommendationCode": item.recommendation.code,
                    "potentialSavingsKwh": float(item.energy.potential_savings_kwh),
                },
            }
            for item in report.rooms
        ],
        "ai": disconnected_ai(),
    }
