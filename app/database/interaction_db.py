from .expense import Expense
from sqlalchemy.orm import Session
from sqlalchemy import select
from .conn_db import engine, DictTable, MainTable


def get_or_create_item_id(session: Session, item_name: str, category_name: str = None) -> int:
    """
    Ищет товар в справочнике. Если нет — создает.
    Возвращает ID записи из DictTable.
    """
    clean_name = item_name.strip().lower()

    # 1. Пытаемся найти
    stmt = select(DictTable).where(DictTable.item == clean_name)
    existing_item = session.execute(stmt).scalar_one_or_none()

    if existing_item:
        # Если пришла категория (флаг был True), обновляем её
        if category_name:
            existing_item.category = category_name.strip().lower()
        return existing_item.id

    # 2. Если не нашли — создаем новый товар
    new_dict_item = DictTable(
        item=clean_name,
        category=category_name.strip().lower() if category_name else None
    )
    session.add(new_dict_item)
    session.flush()  # Чтобы получить новый ID
    return new_dict_item.id


def add_new_data(instance: Expense):
    with Session(engine) as session:
        try:
            # 1. Сначала разбираемся со справочником через вашу функцию
            # Если flag=True, она обновит категорию, если False — просто найдет/создаст заготовку
            item_id = get_or_create_item_id(
                session,
                instance.item,
                instance.category if instance.flag else None
            )

            # 2. Создаем запись в MainTable
            # Мы передаем только те данные, которые относятся к факту траты
            new_record = MainTable(
                price=instance.price,
                raw=instance.raw,
                user_id=instance.user_id,
                item_id=item_id  # Тот самый ID, который мы только что получили
            )

            session.add(new_record)
            session.commit()

        except Exception as e:
            session.rollback()
            print(f"Ошибка сохранения: {e}")

