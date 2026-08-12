"""
Alembic environment — wired to app.models (so autogenerate sees every
table) and to app.config.settings (so the connection string always comes
from .env / DATABASE_URL, never from a hard-coded value in this repo).

IMPORTANT: the database URL is passed DIRECTLY to create_engine() /
context.configure() below — it is deliberately never stored via
config.set_main_option("sqlalchemy.url", ...) or read back via
config.get_main_option(...). Alembic's Config object is backed by Python's
configparser, which applies %-interpolation to every value — so a URL
containing a literal '%' (extremely common: URL-encoded passwords almost
always contain one, e.g. '%40' for '@' or '%25' for a literal '%') raises
`ValueError: invalid interpolation syntax` the moment it's stored there,
regardless of whether the URL itself is correctly percent-encoded. This
was caught by testing against a real password containing '%' — see
docs/architecture/decision-log.md for the full account.
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool

from alembic import context

# Make `app.*` importable regardless of the working directory this is run from.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings  # noqa: E402
from app.models import Base  # noqa: E402  (importing this populates Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
DATABASE_URL = settings.database_url  # kept as a plain Python variable — never
# passed through config.set_main_option(); see module docstring above.

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
