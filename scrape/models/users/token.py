from pydantic import BaseModel, EmailStr
from datetime import datetime

class TokenData(BaseModel):
    email: EmailStr


class AuthToken(BaseModel):
    access_token: str
    token_type: str
    access_token_expires: datetime
