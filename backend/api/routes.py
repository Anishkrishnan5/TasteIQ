from fastapi import APIRouter, Depends
from core.errors import BadRequestError

router = APIRouter()


def get_app_version():
    return "0.1.0"


@router.get("/health")
def health(version: str = Depends(get_app_version)):
    return {
        "status": "ok",
        "version": version
    }


@router.get("/test-error")
def test_error(q: int):
    if q < 0:
        raise BadRequestError("q must be non-negative")
    return {"q": q}
