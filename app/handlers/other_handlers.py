from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from app.services.notes_handling import form_expense_instance, process_msg_to_expenses

from app.keyboards import add_subname_kb, category_choice_kb
from app.lexicon import *
from app.database import no_subs, DB_Manager
from app.database.expense import Expense
from app.database.functions import get_item_category_map
from app.database.interaction_db import add_new_data
from app.database.models import CatTable
from app.filters import IsAdmin
from app import config
from app.ml.categorizer import categorizer
from app.services.fuzzy_wuzzy import fuzzy_root

# -------------------------------------------------
# CONFIG & ROUTER
# -------------------------------------------------

router = Router()

_conf = config.load_config(None)
router.message.filter(IsAdmin(_conf.tg_bot.admin_ids))


# -------------------------------------------------
# HELPERS
# -------------------------------------------------


def get_user_id(event: Message | CallbackQuery) -> int:
    return event.from_user.id


async def ask_next_item(message: Message, user_id: int, *, edit: bool = False):
    """
    Показывает следующий товар без категории.
    """

    item = no_subs.peek(user_id)

    if not item:
        return await message.answer("✅ Все траты обработаны!")

    text = f"Добавить категорию товару: <b>{item[2]}</b>?"
    reply_markup = add_subname_kb(**LEXICON_SUBNAMES)

    method = message.edit_text if edit else message.answer
    await method(text, reply_markup=reply_markup)


async def get_choice_categories(db: DB_Manager, item_name: str) -> dict[str, str | None]:

    """
    Предлагает категории пресказанные нейросетью(переобучается автоматически) или с помощью размытого поиска(rapidfuzzy)
    """
    ml_category = None
    fuzzy_category = None

    async with db.get_session() as session:
        ml_result = categorizer.predict(item_name)
        if ml_result.get("cat_id"):
            ml_category = await session.scalar(
                select(CatTable.cat).where(CatTable.id == ml_result["cat_id"])
            )

        item_to_category = await get_item_category_map(session)
        guess = await fuzzy_root(item_name, item_to_category)
        if guess:
            fuzzy_category = guess["category"]

    return {"ml": ml_category, "fuzzy": fuzzy_category}


async def ask_choice(
    message: Message, user_id: int, db: DB_Manager, *, edit: bool = False
):

    item = no_subs.peek(user_id)

    if not item:
        return await message.answer("✅ Все траты обработаны!")

    item_name = item[0]
    categories = await get_choice_categories(db, item_name)

    text = f"Выбери категорию для товара: <b>{item[2]}</b>"
    reply_markup = category_choice_kb(categories["ml"], categories["fuzzy"])

    method = message.edit_text if edit else message.answer
    await method(text, reply_markup=reply_markup)


async def proceed_to_next(callback: CallbackQuery, db: DB_Manager):
    """
    Унифицированный переход к следующему элементу очереди.
    """
    user_id = get_user_id(callback)

    if not no_subs.is_empty(user_id):
        await ask_choice(callback.message, user_id, db, edit=True)


# -------------------------------------------------
# MESSAGES
# -------------------------------------------------


@router.message(F.text)
async def add_note(message: Message, db: DB_Manager):
    user_id = get_user_id(message)
    async with db.get_session() as session:
        categories = await process_msg_to_expenses(session, message.text, user_id)

    if categories:
        await message.answer(f"Добавлено в: <b>{categories}</b>")

    if not no_subs.is_empty(user_id):
        await ask_choice(message, user_id, db)


@router.message()
async def ignore_others(message: Message):
    """
    Игнорируем остальные сообщения.
    """
    pass


# -------------------------------------------------
# CALLBACKS — CANCEL / BACK
# -------------------------------------------------


@router.callback_query(F.data == "cancel")
async def cancel_expense(callback: CallbackQuery, db: DB_Manager):
    user_id = get_user_id(callback)

    skipped = no_subs.dequeue(user_id)
    skipped_name = skipped[2] if skipped else "..."

    await callback.message.answer(f"❌ Отменено для: <b>{skipped_name}</b>")
    await callback.answer()

    await proceed_to_next(callback, db)


@router.callback_query(F.data.in_({"correct", "manual_category"}))
async def back_to_main_menu(callback: CallbackQuery):
    await ask_next_item(callback.message, get_user_id(callback), edit=True)
    await callback.answer()


# -------------------------------------------------
# CALLBACKS — GROUP SWITCH
# -------------------------------------------------


@router.callback_query(F.data.in_({"food", "non_food"}))
async def process_group_press(callback: CallbackQuery):
    user_id = get_user_id(callback)

    item = no_subs.peek(user_id)
    if not item:
        return await callback.answer("Нет данных")

    lexicon = LEXICON_FOOD if callback.data == "food" else LEXICON_NONFOOD

    await callback.message.edit_text(
        text=f"Выбери подкатегорию для: <b>{item[2]}</b>",
        reply_markup=add_subname_kb(**lexicon),
    )

    await callback.answer()


# -------------------------------------------------
# CALLBACKS — CATEGORY SAVE
# -------------------------------------------------


@router.callback_query(F.data.in_(LEXICON_KEYS))
async def category_select(callback: CallbackQuery, db: DB_Manager):
    user_id = get_user_id(callback)

    expense = form_expense_instance(no_subs, callback)

    if not expense:
        return await callback.answer("Ошибка сохранения", show_alert=True)

    async with db.get_session() as session:
        await add_new_data(session, expense)
    no_subs.dequeue(user_id)

    await callback.message.answer(f"Сохранено: {expense.category}")
    await callback.answer()

    await proceed_to_next(callback, db)


@router.callback_query(F.data.in_({"choice:ml", "choice:fuzzy"}))
async def suggested_category_select(callback: CallbackQuery, db: DB_Manager):
    user_id = get_user_id(callback)
    item = no_subs.peek(user_id)

    if not item:
        return await callback.answer("Нет данных", show_alert=True)

    source = callback.data.split(":", 1)[1]
    categories = await get_choice_categories(db, item[0])
    category_name = categories.get(source)

    if not category_name:
        return await callback.answer("Не получилось определить категорию", show_alert=True)

    name, price, raw_message = item
    expense = Expense(
        raw=raw_message,
        user_id=user_id,
        item=name,
        category=category_name,
        price=price,
        flag=True,
    )

    async with db.get_session() as session:
        await add_new_data(session, expense)
    no_subs.dequeue(user_id)

    await callback.message.answer(f"Сохранено: {expense.category}")
    await callback.answer()

    await proceed_to_next(callback, db)


# -------------------------------------------------
# CALLBACKS — PAGINATION
# -------------------------------------------------


@router.callback_query(F.data == "close")
async def close_pagination(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    await callback.answer()
