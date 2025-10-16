from sqlalchemy import func
from .conn_db import session, DictTable, MainTable
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from services import get_month_range, get_week_range


def get_cumulative_data(category: str):
    today = date.today()
    # период: от 1-го числа прошлого месяца до конца прошлого месяца
    start_date = today.replace(day=1) - relativedelta(months=1)
    end_date = today.replace(day=1) - relativedelta(days=1)

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
    table_last_id = session.query(
        func.max(MainTable.id)
    ).scalar()  # получаю id последней записи в таблице
    main_name_query = (
        session.query(MainTable).filter(MainTable.id == table_last_id).scalar()
    )
    main_name = main_name_query.name

    dict_last_id = session.query(
        func.max(DictTable.id)
    ).scalar()  # получаю id последней записи в словаре
    dict_name_query = (
        session.query(DictTable).filter(DictTable.id == dict_last_id).scalar()
    )
    dict_name = dict_name_query.name

    if dict_name == main_name:
        session.delete(main_name_query)
        session.delete(dict_name_query)
        print("удалил из словаря и БД")
    else:
        session.delete(main_name_query)
        print("удалил из БД")
    session.commit()
    session.close()
    return main_name
