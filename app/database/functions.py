from sqlalchemy import select, func, Float
from .models import DictTable, MainTable, CatTable, UserTable
from datetime import datetime, timedelta, date, time
from app.services.aux_functions import (
    get_month_range,
    get_week_range,
    get_previous_n_month_ranges,
)
from app.database import refund


async def get_cumulative_data(session, category: str, month: str):
    # Предполагаем, что get_month_range возвращает объекты date или datetime
    start_date, end_date = get_month_range(month)

    # Убираем лишний async with session, так как сессия пришла снаружи уже открытой
    stmt = (
        select(
            func.date(MainTable.created).label("day"),
            func.cast(func.sum(MainTable.price), Float).label("daily_total"),
        )
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .where(
            CatTable.cat == category,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
        )
        .group_by(func.date(MainTable.created))
        .order_by(func.date(MainTable.created))
    )

    result = await session.execute(stmt)
    rows = result.all()  # Получаем все строки

    if not rows:
        return [], []

    days = []
    cumulative = []
    total = 0.0

    for r in rows:
        # Обработка даты
        if isinstance(r.day, str):
            day_obj = datetime.strptime(r.day, "%Y-%m-%d").date()
        else:
            day_obj = r.day  # SQLAlchemy часто сам конвертирует в date объект

        days.append(day_obj.day)

        # Суммируем
        total += float(r.daily_total or 0)
        cumulative.append(round(total, 2))

    return days, cumulative


async def get_three_month_avg(session, category: str, month: str) -> float:
    # Получаем общий диапазон за 3 месяца (от начала самого раннего до конца выбранного)
    ranges = get_previous_n_month_ranges(month, 3)
    if not ranges:
        return 0.0

    overall_start = ranges[-1][0]  # начало самого старого месяца
    overall_end = ranges[0][1]  # конец текущего выбранного месяца

    stmt = (
        select(func.coalesce(func.sum(MainTable.price), 0))
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .where(
            CatTable.cat == category,
            MainTable.created >= overall_start,
            MainTable.created <= overall_end,
        )
    )

    result = await session.execute(stmt)
    total_sum = result.scalar() or 0

    # Делим строго на 3, так как логика функции подразумевает среднее за квартал
    avg = float(total_sum) / 3
    return round(avg, 2)


async def get_all_categories(session) -> list[str]:
    stmt = select(CatTable.cat).distinct().order_by(CatTable.cat)
    result = await session.execute(stmt)
    # scalars() сразу превращает результат в список значений первого столбца
    return list(result.scalars().all())


def format_output(res: list[tuple], width: int = 15) -> list[str]:
    """
    Преобразует кортежи в строки с выравниванием второго значения столбиком.
    :param width: расстояние от начала строки до второго столбца
    """

    filtered = [(k, v) for k, v in res if v is not None]
    if not filtered:
        return ["Трат нет"]

    # Находим длину самого длинного ключа
    max_len = max(len(str(key)) for key, _ in filtered)

    return [f"{key:.<{max_len + 3}} {value}" for key, value in filtered]


async def get_stat_month(session, user_id, mm: str):
    """
    :param user_id: telegram user_id
    :return: cumulative expenses by category for the chosen month
    """
    start_date, end_date = get_month_range(mm)
    stmt = (
        select(
            CatTable.cat,
            func.round(func.sum(MainTable.price), 2).label("total_price"),
        )
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
        )
        .group_by(CatTable.cat)
        .order_by(func.sum(MainTable.price).desc())
    )
    result = await session.execute(stmt)
    month_result = result.all()
    return "\n".join(format_output(month_result))


async def get_stat_week(session, user_id: int) -> list[tuple]:
    """
    :param user_id: telegram user_id
    :return: cumulative expenses by category for the current week
    """
    start_date, end_date = get_week_range()

    stmt = (
        select(
            CatTable.cat,
            func.round(func.sum(MainTable.price), 2).label("total_price"),
        )
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
        )
        .group_by(CatTable.cat)
        .order_by(func.sum(MainTable.price).desc())
    )

    result = await session.execute(stmt)
    week_res = result.all()
    return "\n".join(format_output(week_res))


async def spend_today(session, user_id) -> float:
    start_date = datetime.combine(datetime.now().date(), time.min)

    stmt = (
        select(func.coalesce(func.sum(MainTable.price), 0.0))
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            MainTable.created >= start_date,
        )
    )
    result = await session.scalar(stmt)
    return result


async def spend_week(session, user_id):
    """
    :param user_id: telegram user_id
    :return: The amount of money spent current week
    """
    start_date, end_date = get_week_range()
    stmt = (
        select(func.sum(MainTable.price))
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
        )
    )
    result = await session.execute(stmt)
    week_result = result.scalar()

    return week_result


async def spend_month(session, user_id, month):
    start_date, end_date = get_month_range(month)
    stmt = (
        select(func.round(func.sum(MainTable.price), 2))  # Исправлено закрытие скобок
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
        )
    )
    # Используем scalar(), так как нам нужно одно число
    result = await session.scalar(stmt)
    return result or 0.0


async def get_my_expenses(session, user_id: int):
    """
    получить все траты с начала месяца портянкой с пагинацией
    """
    now = datetime.now()
    start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stmt = (
        select(DictTable.item, MainTable.price)
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= now,
        )
    )
    result = await session.execute(stmt)
    expenses = result.all()
    total = round(sum(r[1] for r in expenses), 2)
    expenses.append(("итого:", total))
    return format_output(expenses)


async def get_my_expenses_group(session, user_id):
    # получить мои траты с начала месяца сгруппированными
    _month = datetime.now().month
    _year = datetime.now().year
    start_date = datetime(_year, _month, 1, hour=0, minute=0, second=0) - timedelta(
        seconds=1
    )
    end_date = datetime.now().replace(second=0, microsecond=0)

    stmt = (
        select(CatTable.cat, func.round(func.sum(MainTable.price), 2))
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
        )
        .group_by(CatTable.cat)
        .order_by(func.sum(MainTable.price).desc())
    )
    result = await session.execute(stmt)
    grouped_res = result.all()

    total = round(sum(item[1] if item else 0 for item in grouped_res), 2)
    grouped_res.append(
        (
            "итого: ",
            total,
        )
    )
    return format_output(grouped_res)


async def get_another(session, user_id, start_date, end_date):
    stmt = (
        select(DictTable.item, func.round(MainTable.price, 2).label("price"))
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            CatTable.cat == "др. продукты",
            MainTable.created.between(start_date, end_date),
        )
    )

    total_stmt = (
        select(func.round(func.sum(MainTable.price), 2))
        .join(DictTable, MainTable.item_id == DictTable.id)
        .join(CatTable, DictTable.cat_id == CatTable.id)
        .join(UserTable, MainTable.user_id == UserTable.id)
        .where(
            UserTable.telegram_id == user_id,
            CatTable.cat == "др. продукты",
            MainTable.created.between(start_date, end_date),
        )
    )

    result = await session.execute(stmt)
    other_list = result.all()
    total = await session.execute(total_stmt)
    other_total = total.scalar() or 0
    other_list.append(("итого:", other_total))

    return "\n".join(format_output(other_list))


async def del_last_note(session, user_id: int):  # Теперь async
    try:
        last_stmt = (
            select(MainTable)
            .join(UserTable, MainTable.user_id == UserTable.id)
            .where(UserTable.telegram_id == user_id)
            .order_by(MainTable.id.desc())
            .limit(1)
        )

        result = await session.execute(last_stmt)  # Добавлен await
        main_obj = result.scalar_one_or_none()

        if not main_obj:
            return None

        item_id = main_obj.item_id
        amount = main_obj.price

        # Если refund асинхронный, добавьте await
        await refund(session, user_id, amount)

        # Проверка на единственное использование
        having_stmt = (
            select(MainTable.item_id)
            .where(MainTable.item_id == item_id)
            .group_by(MainTable.item_id)
            .having(func.count(MainTable.id) == 1)
        )

        check_res = await session.execute(having_stmt)
        is_single_use = check_res.scalar_one_or_none()

        dict_obj = await session.get(DictTable, item_id)  # Добавлен await
        item_name = dict_obj.item if dict_obj else "Неизвестно"

        await session.delete(main_obj)  # Добавлен await

        if is_single_use and dict_obj:
            await session.delete(dict_obj)  # Добавлен await

        # Commit здесь НЕ НУЖЕН, если вы вызываете эту функцию
        # внутри вашего DB_Manager.__aexit__, он сделает это сам.
        # Но если вызываете отдельно — оставьте await session.commit()

        return item_name

    except Exception as e:
        await session.rollback()  # Добавлен await
        print(f"Ошибка удаления: {e}")
        raise  # Лучше пробросить ошибку дальше
