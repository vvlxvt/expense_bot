from dataclasses import dataclass, field
from environs import Env
from sqlalchemy import create_engine, Engine
from aiogram.fsm.state import StatesGroup, State


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]


@dataclass
class Config:
    tg_bot: TgBot
    app_env: str
    base_webhook_url: str
    db_url: str
    db_path: str


def load_config(path: str | None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env("BOT_TOKEN"), admin_ids=list(map(int, env.list("ADMIN_IDS")))
        ),
        app_env=env.str("APP_ENV", "development"),
        base_webhook_url=env.str("BASE_WEBHOOK_URL", ""),
        db_url=f"sqlite+aiosqlite:///{env.str('DB_PATH')}",
        db_path=env.str("DB_PATH"),
    )


class BookState(StatesGroup):
    reading = State()  # Чтение страниц
    grouped = State()  # Группированные траты
