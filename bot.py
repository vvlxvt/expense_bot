import asyncio
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiohttp import web
import aiohttp_jinja2, jinja2, json

from app import config
from app.keyboards import set_main_menu
from app.database.functions import get_cumulative_data
from app import handlers
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from app.services import daily_timer


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

    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.include_router(handlers.user_handlers.router)
    dp.include_router(handlers.other_handlers.router)
    dp.startup.register(on_startup)

    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('app/templates'))

    async def stats_page(request: web.Request):
        category = request.query.get("category")
        month = request.query.get("month")

        # Если нет категории — перенаправляем на категорию "Уля" и текущий месяц
        if not category:
            current_month = datetime.now().strftime("%B").capitalize()  # пример: "October"
            raise web.HTTPFound(f"/stats?category=Уля&month={current_month[:3]}")

        # Если месяц не указан — подставляем текущий
        if not month:
            month = datetime.now().strftime("%b")

        days, cumulative = get_cumulative_data(category, month)

        return aiohttp_jinja2.render_template(
            'stats.html',
            request,
            {
                "category": category,
                "required_month": month,
                "days": json.dumps(days),
                "cumulative": json.dumps(cumulative)
            }
        )

    app.router.add_get('/stats', stats_page)

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    print(f"🚀 Running in {APP_ENV} mode")
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)



if __name__ == "__main__":
    main()
