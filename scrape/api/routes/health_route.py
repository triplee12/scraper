from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/status")
async def health_check() -> dict:
    status = {"status": "ok"}
    return status
