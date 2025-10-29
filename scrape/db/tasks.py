import os
import asyncio
from fastapi import FastAPI
from databases import Database
from scrape.core.configs import DATABASE_URL
from scrape.core.logger import logger

MAX_RETRIES = 5
INITIAL_DELAY = 2


async def connect_to_db(app: FastAPI) -> None:
    db_url = f"""{DATABASE_URL}{os.environ.get("DB_SUFFIX", "")}"""
    database = Database(db_url, min_size=2, max_size=10)

    retries = 0
    delay = INITIAL_DELAY

    while retries < MAX_RETRIES:
        try:
            await database.connect()
            app.state._db = database
            logger.info("✅ Connected to the database.")
            return
        except Exception as e:
            logger.error(f"❌ DB CONNECTION ERROR (attempt {retries + 1})")
            logger.error(e)
            retries += 1

            if retries < MAX_RETRIES:
                logger.info(f"⏳ Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logger.error("🚨 Max retries reached. Could not connect to the database.")
                raise e


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.error("--- DB DISCONNECT ERROR ---")
        logger.error(e)
        logger.error("--- DB DISCONNECT ERROR ---")
