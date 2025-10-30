from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncio
from typing import List, Optional
from scrape.core.logger import logger
from scrape.db.database import get_repository
from scrape.db.repositories.products.product import ProductRepository
from scrape.services.scrapers.amazon_pyw_scraper import AmazonScraper
from scrape.services.scrapers.selenium_amazon import SeleniumAmazonScraper
from scrape.services.wrangling.cleaner import clean_products
from scrape.models.products.product import ProductCreate, ProductUpdate

router = APIRouter()

MAX_CONCURRENT_SCRAPES = 2
scrape_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)

class ScrapeRequest(BaseModel):
    query: str
    proxies: Optional[List[str]] = None
    headless: Optional[bool] = False


@router.post("/selenium")
async def selenium_scrape_endpoint(req: ScrapeRequest):
    async with scrape_semaphore:
        scraper = SeleniumAmazonScraper(headless=req.headless)
        try:
            results = scraper.fetch(req.query)
            scraper.close()
            return {"ok": True, "count": len(results), "results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape")
async def scrape_endpoint(req: ScrapeRequest):
    # throttle concurrent playwright browsers
    async with scrape_semaphore:
        scraper = AmazonScraper(proxies=req.proxies or [], headless=req.headless, max_retries=2)
        try:
            results = await scraper.scrape(req.query)
            return {"ok": True, "count": len(results), "results": results}
        except Exception as e:
            # surface the error in a friendly way
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def scrape_amazon(
    query: str,
    product_repo: ProductRepository = Depends(get_repository(ProductRepository))
):
    logger.info("Scraping Amazon search results for: %s", query)
    scraper = AmazonScraper()
    raw_data = await scraper.scrape(query)
    cleaned_data = clean_products(raw_data)

    for product in cleaned_data:
        product_data = ProductCreate(**product)
        is_created = await product_repo.create_product(
            product_data=product_data
        )

        if not is_created:
            logger.warning("Product already exists: %s", product_data.name)
            product_data = ProductUpdate(**product)
            get_product = await product_repo.get_product_by_url(
                product_url=product_data.url
            )

            if not get_product:
                logger.warning("Product not found by URL: %s", product_data.url)
                continue

            await product_repo.update_product_by_id(
                product_id=get_product.id,
                product_data=product_data
            )

    logger.info("Scraped Amazon search results for: %s", query)
    return {"scraped": len(cleaned_data), "products": cleaned_data}
