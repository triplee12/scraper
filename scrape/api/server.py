import uvicorn
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from fastapi import FastAPI, Request
from scrape.core import configs
from scrape.core import tasks
from scrape.core.logger import logger
from scrape.api.routes.health_route import router as health_router
from scrape.api.routes.scrapers.routes import router as scrapers_router
from scrape.api.routes.products.routes import router as products_router

BASE_PATH = "/v1/scraper"

tags_metadata = [
    {"name": "Health", "description": "Health status of the API Endpoints"},
    {"name": "E-commerce Product Tracker", "description": "Track product prices API Routes"},
]

def get_application():
    fast_api = FastAPI(
        title=configs.PROJECT_NAME,
        version=configs.VERSION,
        docs_url=(
            f"{BASE_PATH}/docs"
        ),
        openapi_url=f"{BASE_PATH}/docs/openapi.json",
        redoc_url=f"{BASE_PATH}/redoc",
    )

    fast_api.add_middleware(
        CORSMiddleware,
        allow_origins=configs.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fast_api.add_middleware(SessionMiddleware, secret_key=configs.SECRET_KEY)

    fast_api.add_event_handler("startup", tasks.create_start_app_handler(fast_api))
    fast_api.add_event_handler("shutdown", tasks.create_stop_app_handler(fast_api))

    fast_api.include_router(health_router, prefix=BASE_PATH)
    fast_api.include_router(scrapers_router, prefix=BASE_PATH)
    fast_api.include_router(products_router, prefix=BASE_PATH)

    return fast_api


app = get_application()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    status_code, detail, url_path = exc.status_code, exc.detail, request.url.path
    logger.error(f"status code: {status_code}, detail: {detail}, url path: {url_path}")
    return JSONResponse(status_code=status_code, content=detail)


def main():
    logger.info("Starting E-commerce Product Price Tracker Application API Platform...")
    uvicorn.run(
        "scrape.api.server:app",
        host="0.0.0.0",
        port=configs.PORT,
        reload=False if configs.ENV.startswith("deployment") else True,
        workers=1
    )


if __name__ == "__main__":
    main()