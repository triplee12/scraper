from typing import Optional
from uuid import UUID
from scrape.core.logger import logger
from scrape.db.repositories.base import BaseRepository


CREATE_SCRAPE_TASK_QUERY = """
    INSERT INTO scrape_tasks (
        source,
        status,
        started_at,
        finished_at,
        user_id
    ) VALUES (
        :source,
        :status,
        :started_at,
        :finished_at,
        :user_id
    ) RETURNING *
"""

GET_SCRAPE_TASK_QUERY = """
    SELECT * FROM scrape_tasks
    WHERE id = :id AND user_id = :user_id
"""

GET_SCRAPE_TASKS_QUERY = """
    SELECT * FROM scrape_tasks
    WHERE user_id = :user_id
    ORDER BY created_at DESC
    LIMIT :limit
"""

GET_SCRAPE_TASKS_COUNT_QUERY = """
    SELECT COUNT(*) FROM scrape_tasks
    WHERE user_id = :user_id
"""

DELETE_SCRAPE_TASK_QUERY = """
    DELETE FROM scrape_tasks
    WHERE id = :id AND user_id = :user_id
"""


class ScrapeTaskRepository(BaseRepository):
    async def create_scrape_task(self, scrape_task: dict):
        logger.info("Creating scrape task: %s", scrape_task)
        try:
            return await self.db.fetch_one(
                CREATE_SCRAPE_TASK_QUERY,
                values=scrape_task
            )
        except Exception as e:
            logger.exception(
                "Error creating scrape task: %s. Exception: %s",
                scrape_task, e
            )
            raise e

    async def get_scrape_task_by_id(self, scrape_task_id: UUID, user_id: UUID):
        logger.info("Getting scrape task by ID: %s", scrape_task_id)
        try:
            task = await self.db.fetch_one(
                GET_SCRAPE_TASK_QUERY,
                values={"id": scrape_task_id, "user_id": user_id}
            )

            if not task:
                logger.warning("Scrape task not found by ID: %s", scrape_task_id)
                return None

            return task
        except Exception as e:
            logger.exception(
                "Error getting scrape task by ID: %s. Exception: %s",
                scrape_task_id, e
            )
            raise e

    async def get_scrape_tasks(self, limit: int, user_id: UUID):
        logger.info("Getting scrape tasks")
        try:
            tasks = await self.db.fetch_all(
                GET_SCRAPE_TASKS_QUERY,
                values={"limit": limit, "user_id": user_id}
            )

            count = await self.db.fetch_one(
                GET_SCRAPE_TASKS_COUNT_QUERY, values={"user_id": user_id}
            )
            count = count[0] if count else 0

            return tasks, count
        except Exception as e:
            logger.exception(
                "Error getting scrape tasks. Exception: %s",
                e
            )
            raise e

    async def delete_scrape_task(self, scrape_task_id: UUID, user_id: UUID):
        logger.info("Deleting scrape task by ID: %s", scrape_task_id)
        try:
            deleted = await self.db.execute(
                DELETE_SCRAPE_TASK_QUERY,
                values={"id": scrape_task_id, "user_id": user_id}
            )

            if not deleted:
                logger.warning("Scrape task not deleted by ID: %s", scrape_task_id)
                return None

            return deleted
        except Exception as e:
            logger.exception(
                "Error deleting scrape task by ID: %s. Exception: %s",
                scrape_task_id, e
            )
            raise e
