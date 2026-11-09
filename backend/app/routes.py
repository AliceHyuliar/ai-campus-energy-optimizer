"""Thin HTTP layer around the deterministic simulation and analysis modules."""

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from backend.app.analysis import analyze_simulation, build_snapshot
from backend.app.errors import error_response
from backend.app.rules import ContractLimitation
from backend.app.simulation import SCENARIO_IDS, SCENARIOS, SimulationUnavailable, load_simulation


def create_router(contracts_dir: Callable[[], Path]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "apiVersion": "1.0", "dataSource": "simulation"}

    @router.get("/api/v1/scenarios")
    def scenarios() -> dict:
        return {
            "apiVersion": "1.0",
            "dataSource": "simulation",
            "scenarios": [
                {"id": scenario_id, "name": name, "description": description}
                for scenario_id, name, description in SCENARIOS
            ],
        }

    @router.get("/api/v1/snapshot", response_model=None)
    def snapshot(
        request: Request, scenario: Annotated[str, Query(min_length=1)]
    ) -> dict | JSONResponse:
        if len(request.query_params.getlist("scenario")) != 1 or not scenario.strip():
            return error_response(
                400, "INVALID_QUERY", "Provide exactly one non-empty scenario parameter."
            )
        if scenario not in SCENARIO_IDS:
            return error_response(
                404, "UNKNOWN_SCENARIO", "Unknown scenario. See /api/v1/scenarios."
            )
        try:
            state = load_simulation(contracts_dir(), scenario)
            return build_snapshot(analyze_simulation(state))
        except (SimulationUnavailable, ContractLimitation):
            return error_response(500, "FIXTURE_UNAVAILABLE", "Simulation fixture is unavailable.")

    return router
