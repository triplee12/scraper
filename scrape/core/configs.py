from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret, CommaSeparatedStrings

config = Config(".env")

DATABASE_URL = config("DATABASE_URL", cast=str)
HOST = config("HOST",cast=str, default="0.0.0.0")
PORT = config("PORT", cast=int, default=8000)