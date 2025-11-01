from typing import Optional
from uuid import UUID
from scrape.core.logger import logger
from scrape.db.repositories.base import BaseRepository

CREATE_USER_QUERY = """
    INSERT INTO users (
        username,
        email,
        hashed_password
    ) VALUES (
        :username,
        :email,
        :hashed_password
    ) RETURNING *
"""

GET_USER_QUERY = """
    SELECT * FROM users
    WHERE id = :id
"""

GET_USER_BY_EMAIL_QUERY = """
    SELECT * FROM users
    WHERE email = :email
""" 


class UserRepository(BaseRepository):
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        logger.info("Getting user by email: %s", email)
        try:
            user = await self.db.fetch_one(
                GET_USER_BY_EMAIL_QUERY,
                values={"email": email}
            )

            if not user:
                logger.warning("User not found by email: %s", email)
                return None

            return user
        except Exception as e:
            logger.exception(
                "Error getting user by email: %s. Exception: %s",
                email, e
            )
            raise e

    async def create_user(self, user: dict) -> dict:
        logger.info("Creating user: %s", user)
        try:
            created_user = await self.db.fetch_one(
                CREATE_USER_QUERY,
                values=user
            )

            if not created_user:
                logger.warning("User not created: %s", user)
                return None

            return created_user
        except Exception as e:
            logger.exception(
                "Error creating user: %s. Exception: %s",
                user, e
            )
            raise e

    async def get_user_by_id(self, user_id: UUID) -> Optional[dict]:
        logger.info("Getting user by ID: %s", user_id)
        try:
            user = await self.db.fetch_one(
                GET_USER_QUERY,
                values={"id": user_id}
            )

            if not user:
                logger.warning("User not found by ID: %s", user_id)
                return None

            return user
        except Exception as e:
            logger.exception(
                "Error getting user by ID: %s. Exception: %s",
                user_id, e
            )
            raise e
