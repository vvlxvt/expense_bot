from aiogram.types import CallbackQuery
from app.database import no_subs,UserQueue, Expense, add_new_data, engine, DictTable, CatTable
from app.lexicon.lexicon import LEXICON_KEYS
import re
from sqlalchemy import select
from sqlalchemy.orm import Session


def make_name_price(note: str) -> tuple[str, float]:
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

def get_subname(item: str) -> str | None:
    """Возвращает текстовое название категории (cat) для товара (item)."""
    with Session(engine) as session:
        query = (
            select(CatTable.cat)
            .join(DictTable)  # Указываем, что таблицы связаны
            .where(DictTable.item == item)
            .limit(1)
        )
        return session.execute(query).scalar_one_or_none()

def process_message_to_expenses(row_messages: str, user_id: int) -> str:
    lines = row_messages.strip().split("\n")
    results = []

    for line in lines:
        if not line.strip():
            continue

        # Парсим название и цену
        item_name, price = make_name_price(line)

        # Проверяем, есть ли уже этот товар в справочнике БД
        category_name = get_subname(item_name)

        if category_name:
            # Сценарий А: Категория известна
            expense = Expense(
                raw=line,
                user_id=user_id,
                item=item_name,
                price=price,
                category=category_name,
                flag=False
            )
            add_new_data(expense)
            results.append(category_name)
        else:
            # Сценарий Б: Новый товар, категории нет
            expense = Expense(
                raw=line,
                user_id=user_id,
                item=item_name,
                price=price,
                category=None,
                flag=False
            )
            # Сохраняем в таблицу Main (с NULL категорией в справочнике)
            add_new_data(expense)

            # Добавляем в ПЕРСОНАЛЬНУЮ очередь пользователя
            # Передаем кортеж, чтобы функция form_expense_instance могла его распарсить
            no_subs.queue(user_id, (expense.item, expense.price, expense.raw))
            results.append("?")

    return ", ".join(results)


def form_expense_instance(no_subs: UserQueue, callback: CallbackQuery) -> Expense | None:
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
        flag=True  # Чтобы закрепить категорию за товаром в БД
    )