from .expense import Expense
from sqlalchemy.orm import Session
from sqlalchemy import select
from .conn_db import engine, DictTable, MainTable, CatTable


def get_or_create_item_id(
    session: Session, item_name: str, category_name: str = None
) -> int:
    clean_item = item_name.strip().lower()

    # 1. Пытаемся найти товар
    stmt = select(DictTable).where(DictTable.item == clean_item)
    existing_item = session.execute(stmt).scalar_one_or_none()

    if existing_item:
        return existing_item.id

    # 2. Если товара нет, ищем/создаем категорию
    cat_id = None
    if category_name:
        clean_cat = category_name.strip().lower()
        # Ищем категорию
        cat_stmt = select(CatTable.id).where(CatTable.cat == clean_cat)
        cat_id = session.execute(cat_stmt).scalar()

        # Если категории нет в базе — создаем её (чтобы не упасть по Foreign Key)
        if not cat_id:
            new_cat = CatTable(cat=clean_cat)
            session.add(new_cat)
            session.flush()
            cat_id = new_cat.id

    # 3. Создаем новый товар
    new_dict_item = DictTable(item=clean_item, cat_id=cat_id)
    session.add(new_dict_item)
    session.flush()
    return new_dict_item.id


def add_new_data(instance: Expense):
    with Session(engine) as session:
        try:
            # 1. Сначала разбираемся со справочником через вашу функцию
            # Если flag=True, она обновит категорию, если False — просто найдет/создаст заготовку
            item_id = get_or_create_item_id(
                session, instance.item, instance.category if instance.flag else None
            )

            # 2. Создаем запись в MainTable
            # Мы передаем только те данные, которые относятся к факту траты
            new_record = MainTable(
                price=instance.price,
                raw=instance.raw,
                user_id=instance.user_id,
                item_id=item_id,  # Тот самый ID, который мы только что получили
            )

            session.add(new_record)
            session.commit()

        except Exception as e:
            session.rollback()
            print(f"Ошибка сохранения: {e}")
