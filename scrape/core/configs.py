from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret, CommaSeparatedStrings

config = Config(".env")

DATABASE_URL = config("DATABASE_URL", cast=str)
HOST = config("HOST",cast=str, default="0.0.0.0")
PORT = config("PORT", cast=int, default=8000)
ENV = config("ENV", cast=str)
PROJECT_NAME = config("PROJECT_NAME", cast=str, default="Scraper")
VERSION = config("VERSION", cast=str, default="0.1.0")
ALLOWED_ORIGINS = config("ALLOWED_ORIGINS", cast=list, default=["*"])
SECRET_KEY = config("SECRET_KEY", cast=Secret, default="development")
JWT_TOKEN_SECRET_KEY = config("JWT_TOKEN_SECRET_KEY", cast=Secret, default="development")
JWT_TOKEN_ALGORITHM = config("JWT_TOKEN_ALGORITHM", cast=str, default="HS256")
ACCESS_TOKEN_EXPIRE_MINS = config("ACCESS_TOKEN_EXPIRE_MINS", cast=int, default=60)
SENDGRID_API_KEY = config("SENDGRID_API_KEY", cast=Secret, default="development")
FROM_EMAIL = config("FROM_EMAIL", cast=str, default="from@development.com")
SUPPORT_EMAIL = config("SUPPORT_EMAIL", cast=str, default="support@development.com")
AWS_REGION = config("AWS_REGION", cast=str, default="us-east-1")
SES_SENDER = config("SES_SENDER", cast=str, default="sender@development.com")
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", cast=Secret, default="development")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", cast=Secret, default="development")
