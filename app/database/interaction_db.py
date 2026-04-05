from sqlalchemy.ext.asyncio import AsyncSession
from .expense import Expense
from sqlalchemy import select, update
from .models import DictTable, MainTable, CatTable, UserTable


async def get_or_create_item_id(
    session: AsyncSession, item_name: str, category_name: str = None
) -> int:
    clean_item = item_name.strip().lower()

    # 1. Пытаемся найти товар
    stmt = select(DictTable).where(DictTable.item == clean_item)
    result = await session.execute(stmt)
    existing_item = result.scalar_one_or_none()

    # Если товар уже есть в справочнике
    if existing_item:
        # Пришел новый выбор категории (после ручного выбора в боте)
        if category_name:
            clean_cat = category_name.strip().lower()

            # Ищем/создаем категорию
            cat_stmt = select(CatTable.id).where(CatTable.cat == clean_cat)
            result = await session.execute(cat_stmt)
            cat_id = result.scalar()

            if not cat_id:
                new_cat = CatTable(cat=clean_cat)
                session.add(new_cat)
                await session.flush()
                cat_id = new_cat.id

            # Обновляем категорию у уже существующего товара, если она ещё не проставлена
            if existing_item.cat_id != cat_id:
                existing_item.cat_id = cat_id
                await session.flush()

        return existing_item.id

    # 2. Если товара нет, ищем/создаем категорию (по возможности)
    # Если категории нет (новый товар, еще не классифицирован) — используем
    # специальную категорию "без категории".
    if category_name:
        clean_cat = category_name.strip().lower()
    else:
        clean_cat = "без категории"

        # Ищем категорию
        # В середине функции, где ищем категорию:
    cat_stmt = select(CatTable.id).where(CatTable.cat == clean_cat)
    result = await session.execute(cat_stmt)  # Добавлен await
    cat_id = result.scalar()

    if not cat_id:
        new_cat = CatTable(cat=clean_cat)
        session.add(new_cat)
        await session.flush()  # Добавлен await
        cat_id = new_cat.id

    # 3. Создаем новый товар
    new_dict_item = DictTable(item=clean_item, cat_id=cat_id)
    session.add(new_dict_item)
    await session.flush()
    return new_dict_item.id


# функции пополнения баланса


async def top_up(session: AsyncSession, user_id, amount):
    await session.execute(
        update(UserTable)
        .where(UserTable.telegram_id == user_id)
        .values(deposit=UserTable.deposit + amount)
    )
    # commit/flush сделает менеджер


# функции списания с баланса
async def spend(session: AsyncSession, user_id: int, amount: float) -> float:
    stmt = select(UserTable).where(UserTable.telegram_id == user_id)
    user = await session.scalar(stmt)

    if not user:
        raise ValueError("User not found")

    user.deposit -= amount
    return user.deposit


async def refund(session: AsyncSession, user_id: int, amount: float):
    user = await session.scalar(
        select(UserTable).where(UserTable.telegram_id == user_id)
    )
    if not user:
        raise ValueError("User not found")
    user.deposit += amount


async def get_balance(session: AsyncSession, user_id: int):
    result = await session.scalar(
        select(UserTable.deposit).where(UserTable.telegram_id == user_id)
    )
    return round(result, 2) if result is not None else 0.0


async def add_new_data(session: AsyncSession, instance: Expense):
    try:
        # 1. Добавляем await везде!
        item_id = await get_or_create_item_id(
            session, instance.item, instance.category if instance.flag else None
        )

        user_stmt = select(UserTable.id).where(
            UserTable.telegram_id == instance.user_id
        )
        user_id = await session.scalar(user_stmt)

        # 2. Списание тоже через await
        await spend(session, instance.user_id, instance.price)

        new_record = MainTable(
            price=instance.price,
            raw=instance.raw,
            user_id=user_id,
            item_id=item_id,
        )

        session.add(new_record)
        # Если вы используете наш контекстный менеджер DB_Manager,
        # коммит произойдет автоматически при выходе из with.
        # Но для надежности в CRUD функциях часто делают flush
        await session.flush()

    except Exception as e:
        await session.rollback()
        print(f"Ошибка сохранения: {e}")
        raise  # Важно пробросить ошибку, чтобы бот узнал о ней
