from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.services import (
    add_new_data,
    form_expense_instance,
    books,
    process_message_to_expenses,
)
from app.keyboards import add_subname_kb
from app.lexicon import *
from app.database import no_subs  # Теперь это UserQueue
from app.filters import IsAdmin
from app import config
from app.keyboards.pagination import create_pagination_keyboard
from app.config.config import GlobalVars

router = Router()
_conf = config.load_config(None)
_ADMIN_IDS = _conf.tg_bot.admin_ids
router.message.filter(IsAdmin(_ADMIN_IDS))


# Вспомогательная функция для обновления сообщения с вопросом
async def ask_next_item(message: Message, user_id: int, is_edit: bool = False):
    item = no_subs.peek(user_id)

    if not item:
        text = "✅ Все траты обработаны!"
        method = message.edit_text if is_edit else message.answer
        return await method(text)

    text = f"Добавить категорию товару: <b>{item[2]}</b>?"
    reply_markup = add_subname_kb(**LEXICON_SUBNAMES)

    method = message.edit_text if is_edit else message.answer
    await method(text, reply_markup=reply_markup)


# --- MESSAGES ---


@router.message(F.text)
async def add_note(message: Message):
    user_id = message.from_user.id
    # get_categories внутри делает add_new_data и наполняет no_subs(user_id)
    all_categories = process_message_to_expenses(message.text, user_id)
    print(all_categories)

    if all_categories:
        await message.answer(f"Добавлено в: <b>{all_categories}</b>")

    await ask_next_item(message, user_id)


# --- CALLBACKS: МЕНЮ И ОТМЕНА ---


@router.callback_query(F.data == "cancel")
async def cancel_expense(callback: CallbackQuery):
    user_id = callback.from_user.id
    skipped = no_subs.dequeue(user_id)
    text = f"Отменено для: <b>{skipped[2] if skipped else '...'}</b>"
    await callback.answer(text)
    await ask_next_item(callback.message, user_id, is_edit=True)


@router.callback_query(F.data == "correct")
async def back_to_main_menu(callback: CallbackQuery):
    # Возврат к LEXICON_SUBNAMES
    await ask_next_item(callback.message, callback.from_user.id, is_edit=True)
    await callback.answer()


# --- CALLBACKS: ПЕРЕКЛЮЧЕНИЕ ГРУПП ---


@router.callback_query(F.data.in_({"food", "non_food"}))
async def process_group_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    item = no_subs.peek(user_id)
    lexicon = LEXICON_FOOD if callback.data == "food" else LEXICON_NONFOOD

    await callback.message.edit_text(
        text=f"Выбери подкатегорию для: <b>{item[2] if item else ''}</b>",
        reply_markup=add_subname_kb(**lexicon),
    )
    await callback.answer()


# --- CALLBACKS: СОХРАНЕНИЕ КАТЕГОРИИ ---


@router.callback_query(F.data.in_(LEXICON_KEYS))
async def process_category_selection(callback: CallbackQuery):
    user_id = callback.from_user.id

    # form_expense_instance должен использовать peek и возвращать объект Expense
    expense = form_expense_instance(no_subs, callback)
    print(expense)
    if expense:
        add_new_data(expense)
        no_subs.dequeue(user_id)  # Удаляем из очереди только после сохранения

        # Показываем обычное текстовое сообщение в чате
        await callback.message.answer(f"Сохранено: {expense.category}")
        await callback.answer()

        # Сразу переходим к следующему
        await ask_next_item(callback.message, user_id, is_edit=True)
    else:
        await callback.answer("Ошибка сохранения", show_alert=True)


# --- CALLBACKS: ПАГИНАЦИЯ ---


@router.callback_query(F.data.in_({"forward", "backward"}))
async def process_pagination(callback: CallbackQuery):
    user_id = callback.from_user.id
    gv = GlobalVars(user_id)
    pages = books.get(user_id, {})

    if callback.data == "forward" and gv.page < len(pages):
        gv.page += 1
    elif callback.data == "backward" and gv.page > 1:
        gv.page -= 1
    else:
        return await callback.answer("Это крайняя страница")

    await callback.message.edit_text(
        text=pages.get(gv.page, "Нет данных"),
        reply_markup=create_pagination_keyboard(gv.page),
    )
    await callback.answer()


@router.callback_query(F.data == "close")
async def close_pagination(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    await callback.answer()


@router.message()
async def ignore_others(message: Message):
    pass
