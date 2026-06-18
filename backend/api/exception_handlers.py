import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.schemas.simulation import APIResponse, ResponseMetadata

logger = logging.getLogger("axo_agent")


def register_exception_handlers(app: FastAPI):
    """Register all global exception handlers on the app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        message = "; ".join(
            f"{e.get('loc', ['?'])[-1]}: {e.get('msg', 'invalid')}" for e in errors
        )
        response = APIResponse(
            status_code=422,
            message=message,
            data={"errors": errors},
            metadata=ResponseMetadata(),
        )
        return JSONResponse(status_code=422, content=response.model_dump(mode="json"))

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        response = APIResponse(
            status_code=400,
            message=str(exc),
            metadata=ResponseMetadata(),
        )
        return JSONResponse(status_code=400, content=response.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled error: {exc}")
        response = APIResponse(
            status_code=500,
            message="Internal server error",
            metadata=ResponseMetadata(),
        )
        return JSONResponse(status_code=500, content=response.model_dump(mode="json"))
