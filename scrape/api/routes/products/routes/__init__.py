from fastapi import APIRouter
from scrape.api.routes.products.routes.product import router as product_router


router = APIRouter()
router.include_router(product_router, prefix="/products", tags=["Products"])
