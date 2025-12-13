# alembic/env.py
from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# add project root so `from app.models import Base` works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# import your MetaData (adjust import if your Base is elsewhere)
try:
    from app.models import Base
except Exception as e:
    raise RuntimeError("Failed to import app.models.Base — adjust import in alembic/env.py") from e

target_metadata = Base.metadata

# DB URL: prefer env var, fall back to local connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ledger:ledger_pass@localhost:5432/ledger_db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
