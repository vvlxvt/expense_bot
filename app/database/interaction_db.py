from .expense import Expense
from .conn_db import session, DictTable, MainTable
from sqlalchemy.orm.exc import MultipleResultsFound


def set_value(value, key):
    # добавить значение в словарь товаров и категорий
    prod = DictTable(
        name=value,
        cat=key,
    )
    session.add(prod)
    session.commit()
    session.close()


def get_subname(item):
    try:
        stmt = session.query(DictTable.cat).filter_by(name=item).one_or_none()
    except MultipleResultsFound as e:
        print(
            f"MultipleResultsFound error: {e}"
        )  # Дополнительный код для обработки ошибки
        stmt = session.query(DictTable.cat).filter_by(name=item).first()
    except Exception as e:
        print(f"Unexpected error: {e}")
    return stmt


def add_new_data(instance: Expense):  #
    new_data = MainTable()
    new_data.name = instance.name
    new_data.sub_name = instance.subname
    new_data.price = instance.price
    new_data.created = instance.today
    new_data.raw = instance.raw
    new_data.user_id = instance.user_id
    if instance.flag == True:
        set_value(instance.name, instance.subname)
    session.add(new_data)
    session.commit()
    session.close()


def dict_upload(dict_categories: dict):
    with session:
        for key, value in dict_categories.items():
            for elem in value:
                set_value(elem, key)
        session.commit()
