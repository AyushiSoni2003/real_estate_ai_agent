import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

# Ensure the backend package is importable when Alembic runs from the repo root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_ROOT)

# Load the backend .env file so Alembic can read the same database settings.
load_dotenv(os.path.join(BACKEND_ROOT, ".env"))

# Import the app settings and models so Alembic can target the correct schema.
from backend.app.core.config import settings
from backend.app.core.database import Base

# Import the model modules directly so Alembic sees the ORM tables without relying on the package __init__.
import backend.app.models.agent  # noqa: F401
import backend.app.models.lead  # noqa: F401
import backend.app.models.property  # noqa: F401
import backend.app.models.appointment  # noqa: F401
import backend.app.models.follow_up_log  # noqa: F401
import backend.app.models.message  # noqa: F401
import backend.app.models.property_media  # noqa: F401
import backend.app.models.ai_interaction  # noqa: F401
import backend.app.models.lead_activity  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    config.set_main_option("sqlalchemy.url", url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    config.set_main_option("sqlalchemy.url", url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
