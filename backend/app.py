from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import settings
from core.errors import BadRequestError
from api.routes import router


def create_app():
    app = FastAPI(title=settings.app_name)

    # ---- Exception Handler ----
    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request: Request, exc: BadRequestError):
        return JSONResponse(
            status_code=400,
            content={"error": exc.message}
        )

    # ---- Register Routes ----
    app.include_router(router)

    return app


app = create_app()
