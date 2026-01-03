from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.config import settings


# ---------- Custom Exception ----------
class BadRequestError(Exception):
    def __init__(self, message: str):
        self.message = message


# ---------- App Factory ----------
def create_app():
    app = FastAPI(title=settings.app_name)

    # ---- Exception Handler ----
    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request: Request, exc: BadRequestError):
        return JSONResponse(
            status_code=400,
            content={"error": exc.message}
        )

    # ---- Test Route ----
    @app.get("/test-error")
    def test_error(q: int):
        if q < 0:
            raise BadRequestError("q must be non-negative")
        return {"q": q}

    return app


app = create_app()
