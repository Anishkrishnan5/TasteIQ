import re
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router
from api.schemas import API_SCHEMA_VERSION
from core.config import settings
from personalization.routes import router as personalization_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "Server-Timing"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        supplied_request_id = request.headers.get("X-Request-ID", "")
        request.state.request_id = (
            supplied_request_id
            if re.fullmatch(r"[A-Za-z0-9._-]{1,128}", supplied_request_id)
            else str(uuid4())
        )
        started = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Server-Timing"] = f"total;dur={(perf_counter() - started) * 1000:.3f}"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "schema_version": API_SCHEMA_VERSION,
                "error": {
                    "code": "validation_error",
                    "message": "The request did not match the API contract.",
                    "details": exc.errors(),
                },
                "request_id": request.state.request_id,
            },
        )

    app.include_router(router)
    app.include_router(personalization_router)

    return app


app = create_app()
