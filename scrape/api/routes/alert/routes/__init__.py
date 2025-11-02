from fastapi import APIRouter

from scrape.api.routes.alert.routes.alert import router as alert_router

router = APIRouter()
router.include_router(alert_router, prefix="/alerts", tags=["Alerts"])