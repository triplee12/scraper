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
