from .expense import Expense
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from .conn_db import DictTable, MainTable, CatTable, UserTable
from app.config import engine


def get_or_create_item_id(
    session: Session, item_name: str, category_name: str = None
) -> int:
    clean_item = item_name.strip().lower()

    # 1. Пытаемся найти товар
    stmt = select(DictTable).where(DictTable.item == clean_item)
    existing_item = session.execute(stmt).scalar_one_or_none()

    # Если товар уже есть в справочнике
    if existing_item:
        # Пришел новый выбор категории (после ручного выбора в боте)
        if category_name:
            clean_cat = category_name.strip().lower()

            # Ищем/создаем категорию
            cat_stmt = select(CatTable.id).where(CatTable.cat == clean_cat)
            cat_id = session.execute(cat_stmt).scalar()

            if not cat_id:
                new_cat = CatTable(cat=clean_cat)
                session.add(new_cat)
                session.flush()
                cat_id = new_cat.id

            # Обновляем категорию у уже существующего товара, если она ещё не проставлена
            if existing_item.cat_id != cat_id:
                existing_item.cat_id = cat_id
                session.flush()

        return existing_item.id

    # 2. Если товара нет, ищем/создаем категорию (по возможности)
    # Если категории нет (новый товар, еще не классифицирован) — используем
    # специальную категорию "без категории".
    if category_name:
        clean_cat = category_name.strip().lower()
    else:
        clean_cat = "без категории"

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


# функции пополнения баланса


def top_up(user_id, amount):
    with Session(engine) as session:
        session.execute(
            update(UserTable)
            .where(UserTable.telegram_id == user_id)
            .values(deposit=UserTable.deposit + amount)
        )
        session.commit()


# функции списания с баланса
def spend(session: Session, user_id: int, amount: float) -> float:
    stmt = select(UserTable).where(UserTable.telegram_id == user_id)
    user = session.scalar(stmt)

    if not user:
        raise ValueError("User not found")

    user.deposit -= amount
    return user.deposit


def refund(session: Session, user_id: int, amount: float):
    user = session.scalar(select(UserTable).where(UserTable.telegram_id == user_id))
    if not user:
        raise ValueError("User not found")
    user.deposit += amount


def get_balance(user_id: int):
    with Session(engine) as session:
        return session.scalar(
            select(UserTable.deposit).where(UserTable.telegram_id == user_id)
        )


def add_new_data(instance: Expense):
    with Session(engine) as session:
        try:
            item_id = get_or_create_item_id(
                session, instance.item, instance.category if instance.flag else None
            )

            user_id = session.scalar(
                select(UserTable.id).where(UserTable.telegram_id == instance.user_id)
            )

            # списание
            spend(session, instance.user_id, instance.price)

            new_record = MainTable(
                price=instance.price,
                raw=instance.raw,
                user_id=user_id,
                item_id=item_id,
            )

            session.add(new_record)
            session.commit()

        except Exception as e:
            session.rollback()
            print(f"Ошибка сохранения: {e}")
