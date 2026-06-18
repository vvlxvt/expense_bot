import re

from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.database.expense import Expense
from app.database.functions import get_item_category_map
from app.database.interaction_db import add_new_data
from app.database.models import CatTable, DictTable
from app.database.my_queue import UserQueue, no_subs
from app.lexicon.lexicon import LEXICON_KEYS
from app.ml.categorizer import categorizer
from app.services.fuzzy_wuzzy import fuzzy_root
from app.services.metrics import inc


def make_item_price(note: str) -> tuple[str, float]:
    """Parse an expense line into an item name and price."""
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

        price = float(price_str.replace(",", "."))
        return name.strip(), price
    except (ValueError, TypeError):
        return note.strip(), 0.0


async def get_category(session, item: str) -> str | None:
    """Return the stored category name for an item, if the item is known."""
    clean_item = item.strip().lower()
    query = (
        select(CatTable.cat)
        .join(DictTable)
        .where(DictTable.item == clean_item)
        .limit(1)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def process_msg_to_expenses(
    session, raw_messages: str, user_id: int
) -> str | None:
    """
    Create expense records for known items and queue unknown items for categorization.

    Known items are saved immediately. Unknown items are kept in the per-user queue
    until the user picks a suggested or manual category.
    """
    results: list[str] = []

    for line in filter(None, map(str.strip, raw_messages.splitlines())):
        item_name, price = make_item_price(line)

        ml_result = categorizer.predict(item_name)
        item_to_category = await get_item_category_map(session)
        guess = await fuzzy_root(item_name, item_to_category)
        print("ml_result: ", ml_result)
        print("fuzzy: ", guess)

        category_name = await get_category(session, item_name)

        if category_name:
            expense = Expense(
                raw=line,
                user_id=user_id,
                item=item_name,
                price=price,
                category=category_name,
                flag=False,
            )

            await add_new_data(session, expense)
            inc("expenses_known_total")
            results.append(category_name)
        else:
            no_subs.queue(user_id, (item_name, price, line))
            inc("expenses_queued_total")

    return ", ".join(results) or None


def form_expense_instance(
    no_subs: UserQueue, callback: CallbackQuery
) -> Expense | None:
    """Build an Expense from the queued item and selected manual category callback."""
    user_id = callback.from_user.id
    category_name = LEXICON_KEYS.get(callback.data)

    if not category_name:
        return None

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
        flag=True,
    )
