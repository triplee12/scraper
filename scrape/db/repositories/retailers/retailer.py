from typing import Optional
from uuid import UUID
from scrape.core.logger import logger
from scrape.db.repositories.base import BaseRepository

CREATE_RETAILER_QUERY = """
    INSERT INTO retailers (
        name,
        url,
        logo_url
    ) VALUES (
        :name,
        :url,
        :logo_url
    ) RETURNING *
"""

GET_RETAILERS_QUERY = """
    SELECT * FROM retailers
    ORDER BY created_at DESC
    LIMIT :limit
"""

GET_RETAILERS_COUNT_QUERY = """
    SELECT COUNT(*) FROM retailers
"""

GET_RETAILER_BY_URL_QUERY = """
    SELECT * FROM retailers
    WHERE url = :url
"""

GET_RETAILER_BY_ID_QUERY = """
    SELECT * FROM retailers
    WHERE id = :id
"""

UPDATE_RETAILER_QUERY = """
    UPDATE retailers
    SET name = :name,
        url = :url,
        logo_url = :logo_url
    WHERE id = :id
    RETURNING *
"""


class RetailerRepository(BaseRepository):
    async def get_retailer_by_url(self, url: str) -> Optional[dict]:
        logger.info("Getting retailer by URL: %s", url)
        try:
            retailer = await self.db.fetch_one(
                GET_RETAILER_BY_URL_QUERY,
                values={"url": url}
            )

            if not retailer:
                logger.warning("Retailer not found by URL: %s", url)
                return None

            return retailer
        except Exception as e:
            logger.exception(
                "Error getting retailer by URL: %s. Exception: %s",
                url, e
            )
            raise e

    async def get_retailer_by_id(self, retailer_id: UUID) -> Optional[dict]:
        logger.info("Getting retailer by ID: %s", retailer_id)
        try:
            retailer = await self.db.fetch_one(
                GET_RETAILER_BY_ID_QUERY,
                values={"id": retailer_id}
            )

            if not retailer:
                logger.warning("Retailer not found by ID: %s", retailer_id)
                return None

            return retailer
        except Exception as e:
            logger.exception(
                "Error getting retailer by ID: %s. Exception: %s",
                retailer_id, e
            )
            raise e

    async def create_retailer(self, retailer: dict) -> dict:
        logger.info("Creating retailer: %s", retailer)
        try:
            created_retailer = await self.db.fetch_one(
                CREATE_RETAILER_QUERY,
                values=retailer
            )

            if not created_retailer:
                logger.warning("Retailer not created: %s", retailer)
                return None

            return created_retailer
        except Exception as e:
            logger.exception(
                "Error creating retailer: %s. Exception: %s",
                retailer, e
            )
            raise e

    async def update_retailer(self, retailer: dict) -> dict:
        logger.info("Updating retailer: %s", retailer)
        try:
            updated_retailer = await self.db.fetch_one(
                UPDATE_RETAILER_QUERY,
                values=retailer
            )

            if not updated_retailer:
                logger.warning("Retailer not updated: %s", retailer)
                return None

            return updated_retailer
        except Exception as e:
            logger.exception(
                "Error updating retailer: %s. Exception: %s",
                retailer, e
            )
            raise e

