from fastapi import APIRouter

from scrape.api.routes.scrapers.routes.amazon import router as amazon_router
from scrape.api.routes.scrapers.routes.jumia import router as jumia_router

router = APIRouter()
router.include_router(amazon_router, prefix="/amazon", tags=["Amazon"])
router.include_router(jumia_router, prefix="/jumia", tags=["Jumia"])