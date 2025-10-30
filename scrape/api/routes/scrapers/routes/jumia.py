from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import asyncio
from typing import Optional
from scrape.core.logger import logger
from scrape.db.database import get_repository
from scrape.db.repositories.products.product import ProductRepository
from scrape.services.scrapers.selenium_jumia import JumiaScraper
from scrape.services.wrangling.cleaner import clean_products
from scrape.models.products.product import ProductCreate, ProductUpdate

router = APIRouter()

MAX_CONCURRENT_SCRAPES = 2
scrape_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)

class ScrapeRequest(BaseModel):
    query: str
    headless: Optional[bool] = False


@router.post("/")
async def scrape_amazon(
    query: str = Query(..., example="laptops"),
    product_repo: ProductRepository = Depends(get_repository(ProductRepository))
):
    logger.info("Scraping Amazon search results for: %s", query)
    # https://www.jumia.com.ng/phones-tablets/
    async with scrape_semaphore:
        scraper = JumiaScraper(headless=True)
        try:
            url = f"https://www.jumia.com.ng/?q={query}"
            raw_data = scraper.fetch_products(url, timeout=60)
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
        except Exception as e:
            # surface the error in a friendly way
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            scraper.close()
