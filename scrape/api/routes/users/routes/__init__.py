from fastapi import APIRouter
from scrape.api.routes.users.routes.user import router as user_router

router = APIRouter()

router.include_router(user_router, prefix="/users", tags=["Users"])
