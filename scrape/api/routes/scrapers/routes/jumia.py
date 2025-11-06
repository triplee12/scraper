import asyncio
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from scrape.core.logger import logger
from scrape.db.database import get_repository
from scrape.db.repositories.products.product import ProductRepository
from scrape.db.repositories.retailers.retailer import RetailerRepository
from scrape.db.repositories.products.price_history import PriceHistoryRepository
from scrape.services.scrapers.selenium_jumia import JumiaScraper
from scrape.services.wrangling.cleaner import clean_products
from scrape.models.products.product import ProductCreate

router = APIRouter()

MAX_CONCURRENT_SCRAPES = 2
scrape_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)

class ScrapeRequest(BaseModel):
    query: str
    headless: Optional[bool] = False


@router.post("/")
async def scrape_jumia(
    query: str = Query(..., example="laptops"),
    product_repo: ProductRepository = Depends(get_repository(ProductRepository)),
    retailer_repo: RetailerRepository = Depends(get_repository(RetailerRepository)),
    price_history_repo: PriceHistoryRepository = Depends(get_repository(PriceHistoryRepository))
):
    logger.info("Scraping Amazon search results for: %s", query)
    # https://www.jumia.com.ng/phones-tablets/
    async with scrape_semaphore:
        scraper = JumiaScraper(headless=True)
        try:
            url = f"https://www.jumia.com.ng/{query}"
            retailer = await retailer_repo.get_retailer_by_url(
                "https://www.jumia.com.ng"
            )

            if not retailer:
                raise HTTPException(status_code=404, detail="Retailer not found")

            raw_data = scraper.fetch_products(url, timeout=60)
            cleaned_data = clean_products(raw_data)

            for product in cleaned_data:
                product_data = ProductCreate(**product, retailer_id=retailer["id"])
                is_created = await product_repo.create_product(
                    product_data=product_data
                )

                if is_created:
                    await price_history_repo.create_price_history(
                        product_id=is_created.id,
                        price=product_data.price
                    )

                if not is_created:
                    logger.warning("Product already exists: %s", product_data.name)
                    get_product = await product_repo.get_product_by_url(
                        product_url=product_data.url
                    )

                    if get_product:
                        await price_history_repo.create_price_history(
                            product_id=get_product.id,
                            price=product_data.price
                        )
                    else:
                        logger.warning("Product not found by URL: %s", product_data.url)
                        continue

            logger.info("Scraped Amazon search results for: %s", query)
            return {"scraped": len(cleaned_data), "products": cleaned_data}
        except Exception as e:
            logger.exception("Error scraping Amazon search results for: %s", e)
            raise HTTPException(status_code=500, detail="Server error") from e
        finally:
            scraper.close()
