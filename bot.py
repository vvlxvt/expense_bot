import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiohttp import web
import aiohttp_jinja2, jinja2
from app import config
from app.database import DB_Manager
from app.keyboards import set_main_menu
from app import handlers
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from app.services import daily_timer
from app.web.views import stats_page

conf = config.load_config(None)
TOKEN = conf.tg_bot.token
ADMIN_IDS = conf.tg_bot.admin_ids
BASE_WEBHOOK_URL = conf.base_webhook_url
APP_ENV = conf.app_env

WEBHOOK_PATH = f"/bot{TOKEN}"
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 80


async def on_startup(bot: Bot):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
    await set_main_menu(bot)
    asyncio.create_task(daily_timer())
    print(f"✅ Webhook set for {APP_ENV} environment")


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # 1. Инициализация базы (уже на месте)
    db = DB_Manager(url=conf.db_url, echo=False)

    # 2. Настройка бота
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Передаем db в Dispatcher, чтобы он был доступен во всех хендлерах
    # Это работает для polling и для webhook
    dp["db"] = db

    dp.include_router(handlers.user_handlers.router)
    dp.include_router(handlers.other_handlers.router)
    dp.startup.register(on_startup)

    # 3. Настройка Web App
    app = web.Application()
    app["db"] = db  # Для веба (stats_page)

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("app/templates"))

    # Регистрация маршрутов
    app.router.add_get("/stats", stats_page)
    app.router.add_static("/static/", path="app/static", name="static")

    # ВАЖНО: передаем db в SimpleRequestHandler
    # Аргументы, переданные в kwargs (после bot),
    # прокидываются в хендлеры aiogram при обработке апдейтов.
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp, bot=bot, db=db  # <--- Добавляем сюда
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)

    # Также передаем в setup_application, чтобы aiogram знал о зависимостях
    setup_application(app, dp, bot=bot, db=db)  # <--- И сюда

    # 4. Запуск
    print(f"🚀 Running in {APP_ENV} mode")
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
