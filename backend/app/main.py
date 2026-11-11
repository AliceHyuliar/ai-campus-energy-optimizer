"""Application assembly; deterministic analysis lives outside the HTTP layer."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from backend.app.errors import error_response
from backend.app.routes import create_router
from backend.app.simulation import SCENARIO_IDS as SCENARIO_IDS

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"

app = FastAPI(title="Campus Energy Simulation API", version="1.0.0")
# Resolve the path at request time, preserving the existing missing-source regression test.
app.include_router(create_router(lambda: CONTRACTS_DIR))


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
