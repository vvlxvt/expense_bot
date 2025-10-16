from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]

@dataclass
class Config:
    tg_bot: TgBot
    app_env: str
    base_webhook_url: str
    db_path: str


def load_config(path: str | None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMIN_IDS")))
        ),
        app_env=env.str("APP_ENV", "development"),
        base_webhook_url=env.str("BASE_WEBHOOK_URL", ""),
        db_path=env.str("DB_PATH", "data/real.db")
    )



class GlobalVars:
    _instances = {}

    def __new__(cls, id_):
        # переопределяю создание экземпляра класса
        if id_ not in cls._instances:
            instance = super(GlobalVars, cls).__new__(cls)
            instance.page = None
            cls._instances[id_] = instance
        return cls._instances[id_]


# Пример использования
# g1 = GlobalVars(1)
# g2 = GlobalVars(2)
# g3 = GlobalVars(1)
