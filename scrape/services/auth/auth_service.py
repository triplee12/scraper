from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from scrape.core.configs import ACCESS_TOKEN_EXPIRE_MINS
from scrape.core.configs import JWT_TOKEN_ALGORITHM
from scrape.core.configs import JWT_TOKEN_SECRET_KEY
from scrape.models.users.token import TokenData
from scrape.db.repositories.users.user import UserRepository
from scrape.models.users.user import UserInDB, UserResponse
from scrape.db.database import get_repository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/scraper/users/login")

security = HTTPBearer()

class AuthPassword:
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


class AppJWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            if credentials.scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
            token = credentials.credentials
            return token
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization credentials",
            )

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINS)
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, JWT_TOKEN_SECRET_KEY, algorithm=JWT_TOKEN_ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, JWT_TOKEN_SECRET_KEY, algorithm=JWT_TOKEN_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> TokenData | None:
        try:
            payload = jwt.decode(
                token=token, 
                key=JWT_TOKEN_SECRET_KEY,
                algorithms=[JWT_TOKEN_ALGORITHM],
                options={"verify_exp": True}
            )

            email = payload.get("sub")

            if email is None:
                return None
            return TokenData(email=email)
        except ExpiredSignatureError:
            return None
        except JWTError:
            return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_repository(UserRepository))
) -> UserInDB:

    token_data = AppJWTBearer.decode_token(credentials.credentials)

    if not token_data or not token_data.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Try to login again",
        )

    user = await user_repo.get_user_by_email(email=token_data.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user_public_data = user.model_dump(exclude={"hashed_password"})

    return UserResponse(**user_public_data)
