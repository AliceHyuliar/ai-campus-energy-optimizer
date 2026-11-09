"""Serve approved simulation fixtures without calculating or controlling anything."""

import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"
SCENARIOS = (
    ("idle-room", "Idle room", "Fresh zero occupancy; AC and lights remain on."),
    ("occupied-room", "Occupied room", "An occupied classroom with a class in session."),
    ("class-soon", "Class soon", "An empty room with a class starting in 10 minutes."),
    ("stale-sensor", "Stale sensor", "Occupancy is unknown because its sensor is stale."),
)
SCENARIO_IDS = frozenset(item[0] for item in SCENARIOS)

app = FastAPI(title="Campus Energy Simulation API", version="1.0.0")


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
async def invalid_query(_: Request, __: RequestValidationError) -> JSONResponse:
    return error_response(400, "INVALID_QUERY", "Provide exactly one non-empty scenario parameter.")


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return error_response(404, "NOT_FOUND", "Route not found.")
    if exc.status_code == 405:
        return JSONResponse(
            status_code=405,
            content={"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed."}},
            headers=exc.headers,
        )
    return error_response(exc.status_code, "HTTP_ERROR", "Request failed.")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "apiVersion": "1.0", "dataSource": "simulation"}


@app.get("/api/v1/scenarios")
def scenarios() -> dict:
    return {
        "apiVersion": "1.0",
        "dataSource": "simulation",
        "scenarios": [
            {"id": scenario_id, "name": name, "description": description}
            for scenario_id, name, description in SCENARIOS
        ],
    }


@app.get("/api/v1/snapshot", response_model=None)
def snapshot(
    request: Request, scenario: Annotated[str, Query(min_length=1)]
) -> dict | JSONResponse:
    if len(request.query_params.getlist("scenario")) != 1 or not scenario.strip():
        return error_response(
            400, "INVALID_QUERY", "Provide exactly one non-empty scenario parameter."
        )
    if scenario not in SCENARIO_IDS:
        return error_response(404, "UNKNOWN_SCENARIO", "Unknown scenario. See /api/v1/scenarios.")
    try:
        return json.loads((CONTRACTS_DIR / "examples" / f"{scenario}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return error_response(500, "FIXTURE_UNAVAILABLE", "Simulation fixture is unavailable.")
