from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services import get_categories, add_new_data, form_expense_instance, books
from keyboards import add_subname_kb
from lexicon import *
from database import no_subs
from filters import IsAdmin
from bot import ADMIN_IDS
from keyboards.pagination import create_pagination_keyboard
from config.config import GlobalVars


router: Router = Router()
router.message.filter(IsAdmin(ADMIN_IDS))


@router.message(F.text.lower())
async def add_note(message: Message):
    # обрабатывает любое сообщение пользователя с трат-ой/-ами
    # добавляет трату в БД
    row_message = message.text
    user_id = message.from_user.id
    all_subnames = get_categories(row_message, user_id)
    if all_subnames:
        await message.answer(f" добавлено в категории: <b>{all_subnames}</b>")
    if not no_subs.is_empty():
        await message.answer(
            text=f"добавить категорию товару <b>{no_subs.peek()[2]}</b>?",
            reply_markup=add_subname_kb(**LEXICON_SUBNAMES),
        )


@router.callback_query(F.data == "forward")
async def process_forward_press(callback: CallbackQuery):
    print(callback)
    user_id = callback.from_user.id
    gv = GlobalVars(user_id)
    if gv.page < len(books[user_id]):
        gv.page += 1
        text = books[user_id][gv.page]
        await callback.message.edit_text(
            text=text, reply_markup=create_pagination_keyboard(gv.page)
        )
    await callback.answer()


@router.callback_query(F.data == "backward")
async def process_forward_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    gv = GlobalVars(user_id)
    if gv.page > 1:
        gv.page -= 1
        text = books[user_id][gv.page]
        await callback.message.edit_text(
            text=text, reply_markup=create_pagination_keyboard(gv.page)
        )
    await callback.answer()


@router.callback_query(lambda x: "CLOSE" in x.data)
async def process_stop_press(callback: CallbackQuery):
    await callback.message.delete_reply_markup()


@router.callback_query(F.data == "cancel")
async def cancel_add_expense(callback: CallbackQuery):
    top = no_subs.dequeue()[2]
    # реагирует на нажатие кнопки ДА для выбора категории товару
    if not no_subs.is_empty():
        await callback.message.edit_text(
            f"отменено действие для: <b>{top}</b>\nДобавить категорию товару: <b>"
            f"{no_subs.peek()[2]}</b>",
            reply_markup=add_subname_kb(**LEXICON_SUBNAMES),
        )
    else:
        await callback.message.edit_text(f"отменено действие для: <b>{top}</b>")
        await callback.message.delete_reply_markup()


@router.callback_query(F.data == "correct")
async def correct_add_expense(callback: CallbackQuery):
    # реагирует на нажат ие кнопки ИСПРАВИТЬ для выбора категории товару
    top = no_subs.peek()[2]
    await callback.message.edit_text(
        f"<b> Какую категорию добавить {top} </b>",
        reply_markup=add_subname_kb(**LEXICON_SUBNAMES),
    )
    await callback.answer()


@router.callback_query(F.data == "food")
async def process_basic_food_press(callback: CallbackQuery):
    # реагирует на ключ "food"
    await callback.message.edit_text(
        text=f"выберите подкатегорию для <b>{no_subs.peek()[2]}</b>",
        reply_markup=add_subname_kb(**LEXICON_FOOD),
    )
    await callback.answer()


@router.callback_query(F.data == "non_food")
async def process_basic_nonfood_press(callback: CallbackQuery):
    # реагирует на ключ "non_food"
    await callback.message.edit_text(
        text=f"выберите подкатегорию для <b>{no_subs.peek()[2]}</b>",
        reply_markup=add_subname_kb(**LEXICON_NONFOOD),
    )
    await callback.answer()


@router.callback_query(F.data.in_(LEXICON_KEYS))
async def process_nonfood_press(callback: CallbackQuery):
    """срабатывает на нажатие категорий отсутствующих в словаре, добавляет в ДБ и словарь"""
    expense = form_expense_instance(no_subs, callback)
    add_new_data(expense)
    await callback.message.answer(
        text=f"{expense.name} добавлено в категорию <b>{expense.subname}</b>"
    )
    no_subs.dequeue()
    if no_subs.is_empty():
        await callback.message.answer(text="✅ Все траты добавлены")
        await callback.answer()
    else:
        await callback.message.answer(
            f" выберите категорию для: <b>{no_subs.peek()[2]}</b>",
            reply_markup=add_subname_kb(**LEXICON_SUBNAMES),
        )
        await callback.message.delete_reply_markup()

@router.message()
async def ignore_others(message: Message):
    pass
