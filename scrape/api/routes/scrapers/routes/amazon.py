import asyncio
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from scrape.core.logger import logger
from scrape.db.database import get_repository
from scrape.db.repositories.products.product import ProductRepository
from scrape.db.repositories.retailers.retailer import RetailerRepository
from scrape.db.repositories.products.price_history import PriceHistoryRepository
from scrape.services.scrapers.amazon_pyw_scraper import AmazonScraper
from scrape.services.scrapers.selenium_amazon import AmazonScraper as SeleniumAmazonScraper
from scrape.services.wrangling.cleaner import clean_products
from scrape.models.products.product import ProductCreate

router = APIRouter()

MAX_CONCURRENT_SCRAPES = 2
scrape_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)

class ScrapeRequest(BaseModel):
    query: str
    proxies: Optional[List[str]] = None
    headless: Optional[bool] = False


@router.post("/selenium")
async def selenium_scrape_endpoint(
    req: ScrapeRequest,
    product_repo: ProductRepository = Depends(get_repository(ProductRepository)),
    retailer_repo: RetailerRepository = Depends(get_repository(RetailerRepository)),
    price_history_repo: PriceHistoryRepository = Depends(get_repository(PriceHistoryRepository))
):
    logger.info("Scraping Amazon search results for: %s", req.query)
    async with scrape_semaphore:
        scraper = SeleniumAmazonScraper(headless=req.headless)
        try:
            url = f"https://www.amazon.com/s?k={req.query}"
            retailer = await retailer_repo.get_retailer_by_url(
                "https://www.amazon.com"
            )

            if not retailer:
                raise HTTPException(status_code=404, detail="Retailer not found")

            raw_data = scraper.scrape_search_page(url, limit=20)
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

            logger.info("Scraped Amazon search results for: %s", req.query)
            return {"scraped": len(cleaned_data), "products": cleaned_data}
        except Exception as e:
            logger.exception("Error scraping Amazon: %s", e)
            raise HTTPException(status_code=500, detail="Server error") from e
        finally:
            scraper.close()


@router.post("/playwright")
async def scrape_endpoint(
    req: ScrapeRequest,
    product_repo: ProductRepository = Depends(get_repository(ProductRepository)),
    retailer_repo: RetailerRepository = Depends(get_repository(RetailerRepository)),
    price_history_repo: PriceHistoryRepository = Depends(get_repository(PriceHistoryRepository))
):
    logger.info("Scraping Amazon search results for: %s", req.query)
    async with scrape_semaphore:
        scraper = AmazonScraper(proxies=req.proxies or [], headless=req.headless, max_retries=2)
        try:
            raw_data = await scraper.scrape(req.query)
            cleaned_data = clean_products(raw_data)
            retailer = await retailer_repo.get_retailer_by_url(
                "https://www.amazon.com"
            )

            if not retailer:
                raise HTTPException(status_code=404, detail="Retailer not found")

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

            logger.info("Scraped Amazon search results for: %s", req.query)
            return {"scraped": len(cleaned_data), "products": cleaned_data}
        except Exception as e:
            logger.exception("Error scraping Amazon: %s", e)
            raise HTTPException(status_code=500, detail="Server error") from e


# @router.post("/")
# async def scrape_amazon(
#     query: str,
#     product_repo: ProductRepository = Depends(get_repository(ProductRepository))
# ):
#     logger.info("Scraping Amazon search results for: %s", query)
#     scraper = AmazonScraper()
#     raw_data = await scraper.scrape(query)
#     cleaned_data = clean_products(raw_data)

#     for product in cleaned_data:
#         product_data = ProductCreate(**product)
#         is_created = await product_repo.create_product(
#             product_data=product_data
#         )

#         if not is_created:
#             logger.warning("Product already exists: %s", product_data.name)
#             product_data = ProductUpdate(**product)
#             get_product = await product_repo.get_product_by_url(
#                 product_url=product_data.url
#             )

#             if not get_product:
#                 logger.warning("Product not found by URL: %s", product_data.url)
#                 continue

#             await product_repo.update_product_by_id(
#                 product_id=get_product.id,
#                 product_data=product_data
#             )

#     logger.info("Scraped Amazon search results for: %s", query)
#     return {"scraped": len(cleaned_data), "products": cleaned_data}
