import json
from datetime import datetime
from calendar import month_abbr
import aiohttp_jinja2
from aiohttp import web
from app.database import (
    get_three_month_avg,
    get_cumulative_data,
    get_all_categories,
)


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

    db = request.app["db"]
    async with db.get_session() as session:
        days, cumulative = await get_cumulative_data(session, category, month)
        avg3m = await get_three_month_avg(session, category, month)
        categories = await get_all_categories(session)

    # подготовим список месяцев как сокращения Jan..Dec
    from calendar import month_abbr

    months = [abbr for abbr in month_abbr if abbr]

    return aiohttp_jinja2.render_template(
        "stats.html",
        request,
        {
            "category": category,
            "required_month": month,
            "days": json.dumps(days),
            "cumulative": json.dumps(cumulative),
            "categories": categories,
            "months": months,
            "avg3m": avg3m,
        },
    )
