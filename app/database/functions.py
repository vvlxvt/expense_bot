from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .conn_db import session, DictTable, MainTable, CatTable, engine
from datetime import datetime, timedelta, date, time
from app.services.aux_functions import (
    get_month_range,
    get_week_range,
    get_previous_n_month_ranges,
)


def get_cumulative_data(category: str, month: str):

    start_date, end_date = get_month_range(month)

    # получаем суммы за каждый день по категории
    result = (
        session.query(
            func.DATE(MainTable.created).label("day"),
            func.round(func.sum(MainTable.price), 2).label("daily_total"),
        )
        .filter(MainTable.sub_name == category)
        .filter(
            func.DATE(MainTable.created) >= start_date,
            func.DATE(MainTable.created) <= end_date,
        )
        .group_by(func.DATE(MainTable.created))
        .order_by(func.DATE(MainTable.created))
        .all()
    )
    # если нет данных — вернуть пустое
    if not result:
        return [], []

    # создаём списки для графика
    days = []
    cumulative = []
    total = 0

    for r in result:
        # если база вернула строку — превращаем её в date
        day_value = r.day
        if isinstance(day_value, str):
            from datetime import datetime

            day_value = datetime.strptime(day_value, "%Y-%m-%d").date()

        days.append(day_value.day)
        total += float(r.daily_total)
        cumulative.append(round(total, 2))

    return days, cumulative


def get_three_month_avg(category: str, month: str) -> float:
    """
    Средний расход по категории за предыдущие 3 месяца (по месяцам),
    относительно выбранного месяца. Месяцы без трат учитываются как 0.
    """
    ranges = get_previous_n_month_ranges(month, 3)
    monthly_totals: list[float] = []

    for start_date, end_date in ranges:
        total = (
            session.query(func.coalesce(func.round(func.sum(MainTable.price), 2), 0))
            .filter(MainTable.sub_name == category)
            .filter(
                func.DATE(MainTable.created) >= start_date,
                func.DATE(MainTable.created) <= end_date,
            )
            .scalar()
        )
        monthly_totals.append(float(total or 0))

    if not monthly_totals:
        return 0.0
    avg = sum(monthly_totals) / len(monthly_totals)
    return round(avg, 2)


def get_all_categories() -> list[str]:
    # вернуть список уникальных категорий из основой таблицы
    query = select(CatTable.cat)
    return [row[0] for row in query]


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

    return [f"{key:.<{max_len + 3}} : {value}" for key, value in filtered]


def get_stat_month(mm: str):
    """
    :param user_id: telegram user_id
    :return: cumulative expenses by category for the chosen month
    """
    start_date, end_date = get_month_range(mm)

    with Session(engine) as session:
        stmt = (
            select(
                CatTable.cat,
                func.round(func.sum(MainTable.price), 2).label("total_price"),
            )
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(MainTable.created >= start_date, MainTable.created <= end_date)
            .group_by(CatTable.cat)
            .order_by(func.sum(MainTable.price).desc())
        )
        result = session.execute(stmt).all()
    return "\n".join(format_output(result))


def get_stat_week(user_id: int) -> list[tuple]:
    """
    :param user_id: telegram user_id
    :return: cumulative expenses by category for the current week
    """
    start_date, end_date = get_week_range()

    with Session(engine) as session:
        stmt = (
            select(
                CatTable.cat,
                func.round(func.sum(MainTable.price), 2).label("total_price"),
            )
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(
                MainTable.user_id == user_id,
                MainTable.created >= start_date,
                MainTable.created <= end_date,
            )
            .group_by(CatTable.cat)
            .order_by(func.sum(MainTable.price).desc())
        )

        result = session.execute(stmt).all()
    return "\n".join(format_output(result))


def spend_today(user_id) -> float:
    """
    :param user_id: telegram user_id
    :return: The amount of money spent today
    """
    start_date = datetime.combine(datetime.today(), time.min)

    with Session(engine) as session:
        stmt = select(func.sum(MainTable.price)).where(
            MainTable.user_id == user_id, MainTable.created >= start_date
        )
        result = session.execute(stmt).scalar()
        print(result)
    return result


def spend_week(user_id):
    """
    :param user_id: telegram user_id
    :return: The amount of money spent current week
    """
    start_date, end_date = get_week_range()
    with Session(engine) as session:
        stmt = select(func.sum(MainTable.price)).where(
            MainTable.user_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
        )
        result = session.execute(stmt).scalar()

    return result


def spend_month(month):
    start_date, end_date = get_month_range(month)
    with Session(engine) as session:
        stmt = select(func.sum(MainTable.price)).where(
            MainTable.created >= start_date, MainTable.created <= end_date
        )
        result = session.execute(stmt).scalar()
    return result


def get_my_expenses(user_id: int):
    """
    получить все траты с начала месяца портянкой с пагинацией
    """
    with Session(engine) as session:
        now = datetime.now()
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stmt = (
            select(CatTable.cat, func.round(func.sum(MainTable.price), 2))
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(
                MainTable.user_id == user_id,
                MainTable.created >= start_date,
                MainTable.created <= now,
            )
            .group_by(CatTable.cat)
            .order_by(func.sum(MainTable.price).desc())
        )
        print(session.execute(stmt).all())
        result = session.execute(stmt).all()
        total = round(sum(price for cat, price in result), 2)
        result.append(("итого:", total))
    return result


def get_my_expenses_group(user_id):
    # получить мои траты с начала месяца сгруппированными
    _month = datetime.now().month
    _year = datetime.now().year
    start_date = datetime(_year, _month, 1, hour=0, minute=0, second=0) - timedelta(
        seconds=1
    )
    end_date = datetime.now().replace(second=0, microsecond=0)

    with Session(engine) as session:
        stmt = (
            select(CatTable.cat, func.round(func.sum(MainTable.price), 2))
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(
                MainTable.user_id == user_id,
                MainTable.created >= start_date,
                MainTable.created <= end_date,
            )
            .group_by(CatTable.cat)
            .order_by(func.sum(MainTable.price).desc())
        )
        result = session.execute(stmt).all()

    total = round(sum(item[1] if item else 0 for item in result), 2)
    result.append(
        (
            "итого: ",
            total,
        )
    )
    return "\n".join(format_output(result))


def get_another(start_date, end_date):
    # вывести траты из категории Другое
    result = (
        session.query(MainTable.name, func.round(MainTable.price, 2))
        .filter(MainTable.created.between(start_date, end_date))
        .filter(MainTable.sub_name.in_(["другое", "др. продукты"]))
        .order_by(MainTable.price.desc())
        .all()
    )
    return "\n".join(format_output(result))


def del_last_note():
    with Session(engine) as session:
        # 1. Находим последнюю запись в основной таблице
        # Подгружаем связанный объект item сразу, чтобы не делать лишних запросов
        stmt = select(MainTable).order_by(MainTable.id.desc()).limit(1)
        last_note = session.execute(stmt).scalar_one_or_none()

        if not last_note:
            print("База данных пуста")
            return None

        # Сохраняем информацию для возврата
        item_name = "Неизвестно"

        # 2. Получаем объект из DictTable по ForeignKey
        stmt_dict = select(DictTable).where(DictTable.id == last_note.item_id)
        dict_entry = session.execute(stmt_dict).scalar_one_or_none()

        if dict_entry:
            item_name = dict_entry.item
            session.delete(last_note)
            session.delete(dict_entry)
            print(f"Удалено из БД и словаря: ...{item_name}")
        else:
            session.delete(last_note)
            print("Запись в MainTable удалена, связанный item не найден")

        session.commit()
        return item_name
