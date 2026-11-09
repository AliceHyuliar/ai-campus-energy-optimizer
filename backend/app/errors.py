"""Shared HTTP error envelope; retain the frozen response shapes and messages."""

from fastapi.responses import JSONResponse


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})
