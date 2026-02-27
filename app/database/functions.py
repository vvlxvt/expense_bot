from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .conn_db import session, DictTable, MainTable, CatTable, engine
from datetime import datetime, timedelta, date, time
from app.services.aux_functions import (
    get_month_range,
    get_week_range,
    get_previous_n_month_ranges,
)


from sqlalchemy import select, func
from datetime import datetime


def get_cumulative_data(category: str, month: str):
    start_date, end_date = get_month_range(month)

    with Session(engine) as session:
        stmt = (
            select(
                func.date(MainTable.created).label("day"),
                func.round(func.sum(MainTable.price), 2).label("daily_total"),
            )
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(
                CatTable.cat == category,
                MainTable.created.between(start_date, end_date),
            )
            .group_by(func.date(MainTable.created))
            .order_by(func.date(MainTable.created))
        )

        result = session.execute(stmt).all()

    if not result:
        return [], []

    days = []
    cumulative = []
    total = 0

    for r in result:
        day_value = r.day

        if isinstance(day_value, str):
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

    with Session(engine) as session:
        for start_date, end_date in ranges:
            stmt = (
                select(func.coalesce(func.sum(MainTable.price), 0))
                .join(DictTable, MainTable.item_id == DictTable.id)
                .join(CatTable, DictTable.cat_id == CatTable.id)
                .where(
                    CatTable.cat == category,
                    MainTable.created.between(start_date, end_date),
                )
            )

            total = session.execute(stmt).scalar()
            monthly_totals.append(float(total))

    if not monthly_totals:
        return 0.0

    avg = sum(monthly_totals) / len(monthly_totals)
    return round(avg, 2)


def get_all_categories() -> list[str]:
    # вернуть список уникальных категорий из основой таблицы
    with Session(engine) as session:
        stmt = select(CatTable.cat)
        result = session.execute(stmt).all()
        return [row[0] for row in result]


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


def get_stat_month(user_id, mm: str):
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


def spend_month(user_id, month):
    start_date, end_date = get_month_range(month)
    with Session(engine) as session:
        stmt = select(func.round(func.sum(MainTable.price)), 2).where(
            MainTable.user_id == user_id,
            MainTable.created >= start_date,
            MainTable.created <= end_date,
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
            select(DictTable.item, MainTable.price)
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(
                MainTable.user_id == user_id,
                MainTable.created >= start_date,
                MainTable.created <= now,
            )
        )
        result = session.execute(stmt).all()
        total = round(sum(r[1] for r in result), 2)
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


def get_another(user_id, start_date, end_date):
    with Session(engine) as session:
        stmt = (
            select(DictTable.item, func.round(MainTable.price, 2).label("price"))
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(
                MainTable.user_id == user_id,
                CatTable.cat == "др. продукты",
                MainTable.created.between(start_date, end_date),
            )
        )

        total_stmt = (
            select(func.round(func.sum(MainTable.price), 2))
            .join(DictTable, MainTable.item_id == DictTable.id)
            .join(CatTable, DictTable.cat_id == CatTable.id)
            .where(
                MainTable.user_id == user_id,
                CatTable.cat == "др. продукты",
                MainTable.created.between(start_date, end_date),
            )
        )

        result = session.execute(stmt).all()
        total = session.execute(total_stmt).scalar() or 0

        result.append(("итого:", total))

    return "\n".join(format_output(result))


from sqlalchemy import select, func


def del_last_note():
    with Session(engine) as session:
        # 1️⃣ получаем последнюю запись
        last_stmt = select(MainTable).order_by(MainTable.id.desc()).limit(1)

        main_obj = session.execute(last_stmt).scalar_one_or_none()

        if not main_obj:
            print("База данных пуста")
            return None

        item_id = main_obj.item_id

        # 2️⃣ проверяем через HAVING, единственное ли использование
        having_stmt = (
            select(MainTable.item_id)
            .where(MainTable.item_id == item_id)
            .group_by(MainTable.item_id)
            .having(func.count(MainTable.id) == 1)
        )

        is_single_use = session.execute(having_stmt).scalar_one_or_none()

        # получаем имя
        item_name = session.get(DictTable, item_id)
        item_name = item_name.item if item_name else "Неизвестно"

        # 3️⃣ удаляем основную запись
        session.delete(main_obj)

        # 4️⃣ если item использовался один раз — удаляем и его
        if is_single_use:
            dict_obj = session.get(DictTable, item_id)
            if dict_obj:
                session.delete(dict_obj)
                print(f"Удалено из main и items: ...{item_name}")
        else:
            print(f"Удалено только из main: ...{item_name}")

        session.commit()
        return item_name
