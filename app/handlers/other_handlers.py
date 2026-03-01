from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.services import (
    add_new_data,
    form_expense_instance,
    process_msg_to_expenses,
)

from app.keyboards import add_subname_kb
from app.lexicon import *
from app.database import no_subs
from app.filters import IsAdmin
from app import config

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


async def proceed_to_next(callback: CallbackQuery):
    """
    Унифицированный переход к следующему элементу очереди.
    """
    user_id = get_user_id(callback)

    if not no_subs.is_empty(user_id):
        await ask_next_item(callback.message, user_id, edit=True)


# -------------------------------------------------
# MESSAGES
# -------------------------------------------------


@router.message(F.text)
async def add_note(message: Message):
    user_id = get_user_id(message)

    categories = process_msg_to_expenses(message.text, user_id)

    if categories:
        await message.answer(f"Добавлено в: <b>{categories}</b>")

    if not no_subs.is_empty(user_id):
        await ask_next_item(message, user_id)


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
async def cancel_expense(callback: CallbackQuery):
    user_id = get_user_id(callback)

    skipped = no_subs.dequeue(user_id)
    skipped_name = skipped[2] if skipped else "..."

    await callback.message.answer(f"❌ Отменено для: <b>{skipped_name}</b>")
    await callback.answer()

    await proceed_to_next(callback)


@router.callback_query(F.data == "correct")
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
async def category_select(callback: CallbackQuery):
    user_id = get_user_id(callback)

    expense = form_expense_instance(no_subs, callback)

    if not expense:
        return await callback.answer("Ошибка сохранения", show_alert=True)

    add_new_data(expense)
    no_subs.dequeue(user_id)

    await callback.message.answer(f"Сохранено: {expense.category}")
    await callback.answer()

    await proceed_to_next(callback)


# -------------------------------------------------
# CALLBACKS — PAGINATION
# -------------------------------------------------


@router.callback_query(F.data == "close")
async def close_pagination(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    await callback.answer()
