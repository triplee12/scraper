from typing import Optional
from uuid import UUID
from scrape.core.logger import logger
from scrape.db.repositories.base import BaseRepository

CREATE_ALERT_QUERY = """
    INSERT INTO alerts (
        user_id,
        product_id,
        target_price,
        is_triggered
    ) VALUES (
        :user_id,
        :product_id,
        :target_price,
        :is_triggered
    ) RETURNING *
"""

GET_ALERTS_QUERY = """
    SELECT * FROM alerts
    WHERE user_id = :user_id
    ORDER BY created_at DESC
    LIMIT :limit
"""

GET_ALERTS_COUNT_QUERY = """
    SELECT COUNT(*) FROM alerts
    WHERE user_id = :user_id
"""

DELETE_ALERT_BY_ID_QUERY = """
    DELETE FROM alerts
    WHERE id = :id AND user_id = :user_id
    RETURNING *
"""


class AlertRepository(BaseRepository):
    async def create_alert(self, alert: dict) -> dict:
        logger.info("Creating alert: %s", alert)
        try:
            created_alert = await self.db.fetch_one(
                CREATE_ALERT_QUERY,
                values=alert
            )

            if not created_alert:
                logger.warning("Alert not created: %s", alert)
                return None

            return created_alert
        except Exception as e:
            logger.exception(
                "Error creating alert: %s. Exception: %s",
                alert, e
            )
            raise e

    async def get_alerts(self, user_id: UUID, limit: int) -> list:
        logger.info("Getting alerts for user: %s", user_id)
        try:
            values = {"user_id": user_id, "limit": limit}
            alerts = await self.db.fetch_all(GET_ALERTS_QUERY, values=values)

            count = await self.db.fetch_one(GET_ALERTS_COUNT_QUERY, values={"user_id": user_id})
            count = count[0] if count else 0

            if len(alerts) == 0:
                logger.warning("No alerts found for user: %s", user_id)
                return [], count

            return alerts, count
        except Exception as e:
            logger.exception(
                "Error getting alerts for user: %s. Exception: %s",
                user_id, e
            )
            raise e

    async def delete_alert_by_id(self, alert_id: UUID, user_id: UUID) -> Optional[dict]:
        logger.info("Deleting alert by ID: %s", alert_id)
        try:
            alert = await self.db.fetch_one(
                DELETE_ALERT_BY_ID_QUERY,
                values={"id": alert_id, "user_id": user_id}
            )

            if not alert:
                logger.warning("Alert not found by ID: %s", alert_id)
                return None

            return alert
        except Exception as e:
            logger.exception(
                "Error deleting alert by ID: %s. Exception: %s",
                alert_id, e
            )
            raise e
