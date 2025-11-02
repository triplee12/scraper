from datetime import datetime
from typing import Optional, List
from uuid import UUID
from asyncpg import UniqueViolationError
from databases import Database
from fastapi import HTTPException, status
from scrape.core.logger import logger
from scrape.db.repositories.base import BaseRepository
from scrape.models.users.user import UserInDB, User, UserPasswordUpdateRequest, UserUpdateRequest

CREATE_USER_QUERY = """
    INSERT INTO users (
        username,
        email,
        hashed_password,
        is_superuser,
        is_admin,
        is_active
    ) VALUES (
        :username,
        :email,
        :hashed_password,
        :is_superuser,
        :is_admin,
        :is_active
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

GET_ALL_USERS_QUERY = """
    SELECT * FROM users
    LIMIT :limit
    OFFSET :offset
"""

COUNT_ALL_USERS_QUERY = """
    SELECT COUNT(*) FROM users
"""

DELETE_USER_QUERY = """
    DELETE FROM users
    WHERE id = :id
    RETURNING *
"""

UPDATE_USER_QUERY = """
    UPDATE users
    SET email = :email, is_superuser = :is_superuser,
    is_admin = :is_admin, is_active = :is_active, username = :username
    WHERE id = :id
    RETURNING *;
"""

UPDATE_USER_PASSWORD_QUERY = """
    UPDATE users
    SET hashed_password = :hashed_password
    WHERE id = :id
    RETURNING *;
"""


class UserRepository(BaseRepository):
    def __init__(self, db: Database):
        super().__init__(db)
        from scrape.services.auth.auth_service import AuthPassword
        self.auth_password = AuthPassword()
        logger.info("User Repository initialized")

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        logger.info("Getting user by email: %s", email)
        try:
            user = await self.db.fetch_one(
                GET_USER_BY_EMAIL_QUERY,
                values={"email": email}
            )

            if not user:
                logger.warning("User not found by email: %s", email)
                return None

            return UserInDB(**user) if user else user
        except Exception as e:
            logger.exception(
                "Error getting user by email: %s. Exception: %s",
                email, e
            )
            raise e

    async def create_user(self, user: User) -> Optional[UserInDB]:
        logger.info("Creating user: %s", user)
        try:
            values = user.model_dump(exclude={"password"})
            values["email"] = user.email.lower()
            hashed_password = self.auth_password.hash_password(user.password)
            values["hashed_password"] = hashed_password
            created_user = await self.db.fetch_one(
                CREATE_USER_QUERY,
                values=values
            )

            if not created_user:
                logger.warning("User not created: %s", user)
                return None

            return UserInDB(**created_user) if created_user else created_user
        except UniqueViolationError as uve:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or username already exists or user with superuser role already exists"
            ) from uve
        except Exception as e:
            logger.exception(
                "Error creating user: %s. Exception: %s",
                user, e
            )
            raise e

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        logger.info("Getting user by ID: %s", user_id)
        try:
            user = await self.db.fetch_one(
                GET_USER_QUERY,
                values={"id": user_id}
            )

            if not user:
                logger.warning("User not found by ID: %s", user_id)
                return None

            return UserInDB(**user) if user else user
        except Exception as e:
            logger.exception(
                "Error getting user by ID: %s. Exception: %s",
                user_id, e
            )
            raise e
    
    async def get_all_users(self, limit: int, offset: int) -> List[UserInDB] | list:
        try:
            logger.info("Getting all users")
            values={"limit": limit, "offset": offset}
            users = await self.db.fetch_all(GET_ALL_USERS_QUERY, values)
            count_users = await self.db.fetch_one(COUNT_ALL_USERS_QUERY)
            count_users = count_users["count"]

            if not users:
                return []

            return [UserInDB(**user) for user in users]
        except Exception as e:
            logger.exception("Error: %s", e)
            raise e

    async def delete_user_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        logger.info("Deleting user by ID: %s", user_id)
        try:
            user = await self.db.fetch_one(
                DELETE_USER_QUERY,
                values={"id": user_id}
            )

            if not user:
                logger.warning("User not found by ID: %s", user_id)
                return None

            return UserInDB(**user) if user else user
        except Exception as e:
            logger.exception(
                "Error deleting user by ID: %s. Exception: %s",
                user_id, e
            )
            raise e

    async def update_user_by_id(self, user_id: UUID, user: UserUpdateRequest):
        try:
            logger.info("Updating user id: %s", user_id)
            values = user.model_dump()
            values["id"] = user_id
            user = await self.db.fetch_one(UPDATE_USER_QUERY, values)

            if not user:
                return None

            return UserInDB(**user)
        except UniqueViolationError as uve:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or username already exists"
            ) from uve
        except Exception as e:
            logger.exception("Error: %s", e)
            raise e

    async def reset_password_token(self, user_id: UUID, token: str, expires_at: datetime):
        logger.info("Updating user reset password token id: %s", user_id)
        try:
            token_data = await self.db.fetch_one(
                """
                INSERT INTO password_resets (user_id, token, expires_at) VALUES (:uid, :token, :exp)
                RETURNING *;
                """,
                {"uid": user_id, "token": token, "exp": expires_at}
            )
            if not token_data:
                return None
            return token_data
        except Exception as e:
            logger.exception("Error: %s", e)
            raise e

    async def get_reset_password_token(self, token: str):
        logger.info("Getting user reset password token: %s", token)
        try:
            token_data = await self.db.fetch_one(
                """
                SELECT * FROM password_resets WHERE token = :token
                """,
                {"token": token}
            )
            if not token_data:
                return None
            return token_data
        except Exception as e:
            logger.exception("Error: %s", e)
            raise e

    async def delete_reset_password_token(self, token: str):
        logger.info("Deleting user reset password token: %s", token)
        try:
            token_data = await self.db.fetch_one(
                """
                DELETE FROM password_resets WHERE token = :token
                """,
                {"token": token}
            )
            if not token_data:
                return None
            return token_data
        except Exception as e:
            logger.exception("Error: %s", e)
            raise e

    async def update_user_password_by_id(self, user_id: UUID, user: UserPasswordUpdateRequest|str):
        try:
            logger.info("Updating user password id: %s", user_id)
            new_password = user if isinstance(user, str) else user.new_password
            hashed_password = self.auth_password.hash_password(new_password)
            values = {
                "id": user_id,
                "hashed_password": hashed_password,
            }
            user = await self.db.fetch_one(UPDATE_USER_PASSWORD_QUERY, values)

            if not user:
                return None

            return UserInDB(**user)
        except Exception as e:
            logger.exception("Error: %s", e)
            raise e
