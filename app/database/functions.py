from sqlalchemy import func, select
from .conn_db import session, DictTable, MainTable
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
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
            func.round(func.sum(MainTable.price), 2).label("daily_total")
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
    result = (
        session.query(MainTable.sub_name)
        .filter(MainTable.sub_name.isnot(None))
        .group_by(MainTable.sub_name)
        .order_by(MainTable.sub_name)
        .all()
    )
    return [row[0] for row in result]

def format_output(res: list[tuple]) -> list[str]:
    # фильтрует пустые значения из запроса по категориям за месяц
    # преобразует список кортежей в список строк
    filtered_res = [(key, value) for key, value in res if value is not None]
    formatted_res = [f"{key}: {value}" for key, value in filtered_res]
    return formatted_res


def get_stat_month(mm: str):
    start_date, end_date = get_month_range(mm)
    result = (
        session.query(MainTable.sub_name, func.round(func.sum(MainTable.price), 2))
        .filter(
            func.DATE(MainTable.created) >= start_date,
            func.DATE(MainTable.created) <= end_date,
        )
        .group_by(MainTable.sub_name)
        .order_by(func.sum(MainTable.price).desc())
        .all()
    )
    return "\n".join(format_output(result))


def get_stat_week(user_id):
    start_date, end_date = get_week_range()
    result = (
        session.query(MainTable.sub_name, func.round(func.sum(MainTable.price), 2))
        .filter(MainTable.user_id == user_id)
        .filter(MainTable.created >= start_date,
                MainTable.created <= end_date)
        .group_by(MainTable.sub_name)
        .order_by(func.sum(MainTable.price).desc())
        .all()
    )
    return "\n".join(format_output(result))


def spend_today(user_id):
    """
    :param user_id: telegram user_id
    :return: The amount of money spent today
    """
    start_date = datetime.today().date()
    end_date = datetime.now().replace(second=0, microsecond=0)
    result = (
        session.query(func.round(func.sum(MainTable.price), 2))
        .filter(MainTable.user_id == user_id)
        .filter(
            func.DATE(MainTable.created) >= start_date,
            func.DATE(MainTable.created) <= end_date,
        )
        .scalar()
    )
    return result


def spend_week(user_id):
    start_date, end_date = get_week_range()
    result = (
        session.query(func.sum(MainTable.price))
        .filter(MainTable.user_id == user_id)
        .filter(
            func.DATE(MainTable.created) >= start_date,
            func.DATE(MainTable.created) <= end_date,
        )
        .scalar()
    )
    return result


def spend_month(month):
    start_date, end_date = get_month_range(month)
    result = (
        session.query(func.round(func.sum(MainTable.price), 2))
        .filter(
            func.DATE(MainTable.created) >= start_date,
            func.DATE(MainTable.created) <= end_date,
        )
        .scalar()
    )
    return result


def get_my_expenses(user_id):
    # получить мои траты с начала месяца
    _month = datetime.now().month
    _year = datetime.now().year
    start_date = datetime(_year, _month, 1, hour=0, minute=0, second=0) - timedelta(
        seconds=1
    )
    end_date = datetime.now().replace(second=0, microsecond=0)

    result: list = (
        session.query(MainTable.name,
                      func.round(MainTable.price, 2))
        .filter(MainTable.user_id == user_id)
        .filter(func.DATE(MainTable.created) >= start_date,
                func.DATE(MainTable.created) <= end_date,)
        .all()
    )
    total = round(sum(item[1] if item else 0 for item in result), 2)
    result.append(
        (
            "итого: ",
            total,
        )
    )
    return result


def get_my_expenses_group(user_id):
    # получить мои траты с начала месяца
    _month = datetime.now().month
    _year = datetime.now().year
    start_date = datetime(_year, _month, 1, hour=0, minute=0, second=0) - timedelta(
        seconds=1
    )
    end_date = datetime.now().replace(second=0, microsecond=0)

    result = (
        session.query(MainTable.sub_name, func.round(func.sum(MainTable.price), 2))
        .filter(MainTable.user_id == user_id)
        .filter(
            func.DATE(MainTable.created) >= start_date,
            func.DATE(MainTable.created) <= end_date,
        )
        .group_by(MainTable.sub_name)
        .order_by(func.sum(MainTable.price).desc())
        .all()
    )
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
    """ф. удаляет из базы данных или из БД и словаря, если было добавление в словарь"""

    main_last_note = select(MainTable.name).order_by(MainTable.id.desc()).limit(1)
    main_name = session.execute(main_last_note).scalar_one_or_none()

    dict_last_note = select(DictTable.name).order_by(DictTable.id.desc()).limit(1)  # получаю id последней записи в словаре
    dict_name = session.execute(dict_last_note).scalar_one_or_none()

    if dict_name == main_name:
        session.delete(main_last_note)
        session.delete(dict_last_note)
        print("удалил из словаря и БД")
    else:
        session.delete(main_last_note)
        print("удалил из БД")
    session.commit()
    session.close()
    return main_name
