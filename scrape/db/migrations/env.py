import logging
import os
import pathlib
import sys
from configparser import RawConfigParser
from logging.config import fileConfig

import alembic
from psycopg import DatabaseError
from sqlalchemy import engine_from_config, create_engine, pool
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from scrape.core.configs import DATABASE_URL, ENV

alembic_ini_path = pathlib.Path(__file__).resolve().parents[1] / "alembic.ini"

raw_cofig = RawConfigParser()
raw_cofig.read(alembic_ini_path)

config = alembic.context.config
config.file_config  = raw_cofig

fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode
    """
    if ENV.startswith("deployment"):
        DB_URL = f"{DATABASE_URL}?sslmode=require"
    else:
        DB_URL = f"{DATABASE_URL}"

    logger.info(f'DB_URL: {DB_URL}')

    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", DB_URL)

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool,
        )

    logger.info(f'connectable: {connectable}')

    with connectable.connect() as connection:
        alembic.context.configure(connection=connection, target_metadata=None)

        with alembic.context.begin_transaction():
            alembic.context.run_migrations()


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    """

    if os.environ.get("TESTING"):
        raise DatabaseError(
            "Running testing migrations offline currently not permitted.")

    alembic.context.configure(url=str(DATABASE_URL))

    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


if alembic.context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()
