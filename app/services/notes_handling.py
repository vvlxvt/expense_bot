from aiogram.types import CallbackQuery
from app.database import (
    no_subs,
    UserQueue,
    Expense,
    add_new_data,
    engine,
    DictTable,
    CatTable,
)
from app.lexicon.lexicon import LEXICON_KEYS
import re
from sqlalchemy import select
from sqlalchemy.orm import Session


def make_item_price(note: str) -> tuple[str, float]:
    """Парсит строку на товар и цену. Возвращает (название, цена)."""
    # Паттерны для "товар цена" и "цена товар"
    pattern_1 = r"(^.+)\s(\d+[\.|,]?\d*)$"
    pattern_2 = r"(^\d+[\.|,]?\d*)\s(.+)$"

    res_1 = re.match(pattern_1, note.strip())
    res_2 = re.match(pattern_2, note.strip())

    try:
        if res_1:
            name, price_str = res_1.groups()
        elif res_2:
            price_str, name = res_2.groups()
        else:
            return note.strip(), 0.0

        # Заменяем запятую на точку и приводим к float
        price = float(price_str.replace(",", "."))
        return name.strip(), price
    except (ValueError, TypeError):
        return note.strip(), 0.0


# def get_category_id_by_name(session: Session, name: str) -> int | None:
#     """Вспомогательная функция для получения ID категории по имени товара."""
#     query = select(DictTable.id).where(DictTable.name == name.strip().lower())
#     return session.execute(query).scalar_one_or_none()


def get_category(item: str) -> str | None:
    """Возвращает текстовое название(cat) из таблицы категории для товара (item)."""
    clean_item = item.strip().lower()
    with Session(engine) as session:
        query = (
            select(CatTable.cat)
            .join(DictTable)  # связь по ForeignKey DictTable.cat_id
            .where(DictTable.item == clean_item)
            .limit(1)
        )
        return session.execute(query).scalar_one_or_none()


def process_msg_to_expenses(raw_messages: str, user_id: int) -> str | None:
    """
    Создает запись о трате ТОЛЬКО один раз:
    - если категория известна -> сразу пишем в БД;
    - если категория неизвестна -> кладём в очередь, ждём выбора, в БД пока не пишем.
    """
    results: list[str] = []

    for line in filter(None, map(str.strip, raw_messages.splitlines())):
        item_name, price = make_item_price(line)
        category_name = get_category(item_name)

        if category_name:
            # Уже знаем категорию: сразу сохраняем
            expense = Expense(
                raw=line,
                user_id=user_id,
                item=item_name,
                price=price,
                category=category_name,
                flag=False,
            )
            add_new_data(expense)
            results.append(category_name)
        else:
            # Категория пока неизвестна: в БД НЕ пишем, только ставим в очередь
            no_subs.queue(user_id, (item_name, price, line))

    return ", ".join(results) or None


def form_expense_instance(
    no_subs: UserQueue, callback: CallbackQuery
) -> Expense | None:
    user_id = callback.from_user.id

    # Ищем значение в "плоском" словаре LEXICON_KEYS
    category_name = LEXICON_KEYS.get(callback.data)

    if not category_name:
        return None  # Если это была кнопка группы, а не категория

    pending_item = no_subs.peek(user_id)
    if not pending_item:
        return None

    name, price, raw_message = pending_item

    return Expense(
        raw=raw_message,
        user_id=user_id,
        item=name,
        category=category_name,
        price=price,
        flag=True,  # Чтобы закрепить категорию за товаром в БД
    )
