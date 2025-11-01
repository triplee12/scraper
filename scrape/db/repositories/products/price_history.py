from typing import Optional
from uuid import UUID
from scrape.core.logger import logger
from scrape.db.repositories.base import BaseRepository

CREATE_PRICE_HISTORY_QUERY = """
    INSERT INTO price_history (
        product_id,
        price
    ) VALUES (
        :product_id,
        :price
    ) RETURNING *
"""

GET_PRICE_HISTORY_QUERY = """
    SELECT * FROM price_history
    WHERE product_id = :product_id
    ORDER BY created_at DESC
    LIMIT :limit
"""

GET_PRICE_HISTORY_COUNT_QUERY = """
    SELECT COUNT(*) FROM price_history
    WHERE product_id = :product_id
"""

DELETE_PRICE_HISTORY_QUERY = """
    DELETE FROM price_history
    WHERE product_id = :product_id
    RETURNING *
"""


class PriceHistoryRepository(BaseRepository):
    async def create_price_history(self, product_id: UUID, price: float) -> Optional[dict]:
        logger.info("Creating price history for product: %s", product_id)
        try:
            price_history = await self.db.fetch_one(
                CREATE_PRICE_HISTORY_QUERY,
                values={"product_id": product_id, "price": price}
            )

            if not price_history:
                logger.warning("Price history not created for product: %s", product_id)
                return None

            return price_history
        except Exception as e:
            logger.exception(
                "Error creating price history for product: %s. Exception: %s",
                product_id, e
            )
            raise e

    async def get_price_history(self, product_id: UUID, limit: int) -> Optional[list]:
        logger.info("Getting price history for product: %s", product_id)
        try:
            price_history = await self.db.fetch_all(
                GET_PRICE_HISTORY_QUERY,
                values={"product_id": product_id, "limit": limit}
            )

            count = await self.db.fetch_one(
                GET_PRICE_HISTORY_COUNT_QUERY,
                values={"product_id": product_id}
            )
            count = count[0] if count else 0

            if not price_history:
                logger.warning("Price history not found for product: %s", product_id)
                return None

            return price_history, count
        except Exception as e:
            logger.exception(
                "Error getting price history for product: %s. Exception: %s",
                product_id, e
            )
            raise e

    async def delete_price_history(self, product_id: UUID) -> Optional[dict]:
        logger.info("Deleting price history for product: %s", product_id)
        try:
            price_history = await self.db.fetch_one(
                DELETE_PRICE_HISTORY_QUERY,
                values={"product_id": product_id}
            )

            if not price_history:
                logger.warning("Price history not deleted for product: %s", product_id)
                return None

            return price_history
        except Exception as e:
            logger.exception(
                "Error deleting price history for product: %s. Exception: %s",
                product_id, e
            )
            raise e