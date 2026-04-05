from sqlalchemy import engine_from_config
from sqlalchemy import pool
from logging.config import fileConfig
from alembic import context
from app.database.models import Base
from app import config

conf = config.load_config(None)
# Alembic конфиг
alembic_cfg = context.config

if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

# Свой конфиг приложения
alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{conf.db_path}")  # ✅

target_metadata = Base.metadata


def run_migrations_offline() -> None:

    url = alembic_cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = print(alembic_cfg.get_main_option("sqlalchemy.url"))
    print("----------------", url)
    connectable = engine_from_config(
        alembic_cfg.get_section(alembic_cfg.config_ini_section, {}),  # ✅
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
