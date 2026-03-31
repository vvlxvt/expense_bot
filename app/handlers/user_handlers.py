from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.filters import IsAdmin
from app.lexicon import LEXICON, LEXICON_MONTH, LEXICON_ANOTHER
from app.keyboards import add_subname_kb, another_kb, one_button_kb
from app.keyboards.pagination import create_pagination_keyboard
from app.database import (
    get_stat_week,
    get_my_expenses,
    get_my_expenses_group,
    get_another,
    del_last_note,
    get_stat_month,
    spend_week,
    spend_month,
    spend_today,
    get_balance,
)
from app.services import prepare_book, get_month_range, books
from app.config import BookState
from app import config
from app.database import top_up

# -----------------------------
# CONFIG
# -----------------------------
_conf = config.load_config(None)
_BASE_WEBHOOK_URL = _conf.base_webhook_url.rstrip("/") if _conf.base_webhook_url else ""
_CHARTS_URL = f"{_BASE_WEBHOOK_URL}/stats" if _BASE_WEBHOOK_URL else "/stats"

router = Router()
router.message.filter(IsAdmin(_conf.tg_bot.admin_ids))


# -----------------------------
# HELPERS
# -----------------------------
def get_user_id(event: Message | CallbackQuery) -> int:
    return event.from_user.id


async def send_page(user_id: int, message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get("page", 0)
    user_pages = books.get(user_id, [])

    if not user_pages:
        return await message.answer("Нет данных")

    page = max(0, min(page, len(user_pages) - 1))
    await state.update_data(page=page)

    text = f"<b>Страница {page + 1}/{len(user_pages)}</b>\n\n{user_pages[page]}"

    # Получаем текущее состояние FSM
    current_state = await state.get_state()

    await message.answer(
        text,
        reply_markup=create_pagination_keyboard(user_id, page, state=current_state),
        parse_mode="HTML",
    )


# -----------------------------
# BASIC COMMANDS
# -----------------------------
@router.message(CommandStart())
async def start(message: Message):
    await message.answer(LEXICON["/start"])


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(LEXICON["/help"])


# -----------------------------
# BALANCE COMMANDS
# -----------------------------


@router.message(Command("deposit"))
async def add_deposit(message: Message):
    try:
        amount = float(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("Введите сумму: /deposit 100")
        return

    user_id = get_user_id(message)
    top_up(user_id, amount)

    await message.answer(f"Баланс пополнен на {amount}")


@router.message(Command("balance"))
async def balance(message: Message):
    user_id = get_user_id(message)
    balance = get_balance(user_id)
    await message.answer(f"Ваш баланс {balance} лари")


# -----------------------------
# CHARTS COMMANDS
# -----------------------------


@router.message(Command("charts"))
async def charts(message: Message):
    keyboard = one_button_kb("Открыть график", _CHARTS_URL)
    await message.answer("Перейдите по ссылке:", reply_markup=keyboard)


# -----------------------------
# EXPENSE COMMANDS
# -----------------------------
@router.message(Command("today"))
async def today(message: Message):
    user_id = get_user_id(message)
    total = spend_today(user_id)
    formatted = message.date.strftime("%d-%m-%Y")
    await message.answer(f"Сегодня <i>{formatted}</i> я потратил/а <b>{total}</b> GEL")


@router.message(Command("week"))
async def week(message: Message):
    user_id = get_user_id(message)
    res = get_stat_week(user_id)
    total = round(spend_week(user_id) or 0, 2)
    await message.answer(f"<b>{res}</b>\nС начала недели потрачено: {total} GEL")


@router.message(Command("month"))
async def choose_month(message: Message):
    await message.answer(
        "За какой месяц показать статистику?",
        reply_markup=add_subname_kb(**LEXICON_MONTH),
    )


@router.message(Command("my_month"))
async def send_book(message: Message, state: FSMContext):
    user_id = get_user_id(message)
    result = get_my_expenses(user_id)
    prepare_book(result, user_id)

    if not books.get(user_id):
        return await message.answer("Нет данных для отображения")

    await state.set_state(BookState.reading)
    await state.update_data(page=0, pages=books[user_id])  # <-- добавили pages
    await send_page(user_id, message, state)


@router.message(Command("tanya"))
async def send_book(message: Message, state: FSMContext):
    user_id = 1194999116
    result = get_my_expenses(user_id)
    prepare_book(result, user_id)

    if not books.get(user_id):
        return await message.answer("Нет данных для отображения")

    await state.set_state(BookState.reading)
    await state.update_data(page=0, pages=books[user_id])  # <-- добавили pages
    await send_page(user_id, message, state)


@router.message(Command("del_last_note"))
async def delete_last(message: Message):
    user_id = get_user_id(message)
    last = del_last_note(user_id)
    await message.answer(f"🗑 Удалена запись: {last}")


# -----------------------------
# UNIVERSAL BOOK HANDLER (READING / GROUPED)
# -----------------------------
@router.callback_query(F.data.in_({"prev", "next", "close", "group"}))
async def book_handler(callback: CallbackQuery, state: FSMContext):
    user_id = get_user_id(callback)
    current_state = await state.get_state()
    data = await state.get_data()

    # -------------------------------
    # Кнопка "close" — завершение FSM
    # -------------------------------
    if callback.data == "close":
        await state.clear()
        await callback.message.delete()
        return await callback.answer()

    # -------------------------------
    # Кнопка "group" — перейти на grouped
    # -------------------------------
    if callback.data == "group":
        result = get_my_expenses_group(user_id)
        prepared_result = "\n".join(result)
        if not result:
            return await callback.answer("Нет данных для группировки", show_alert=True)

        await state.set_state(BookState.grouped)
        await callback.message.edit_text(
            f"<u>Мои траты за текущий месяц:</u>\n{prepared_result}\n",
            reply_markup=create_pagination_keyboard(
                user_id, 0, state=BookState.grouped
            ),
        )
        return await callback.answer()

    # -------------------------------
    # Пагинация для reading
    # -------------------------------
    if current_state != BookState.reading:
        return await callback.answer()

    pages = data.get("pages", [])
    page = data.get("page", 0)

    if not pages:
        await callback.answer("Нет данных для отображения", show_alert=True)
        return await state.clear()

    if callback.data == "next" and page < len(pages) - 1:
        page += 1
    elif callback.data == "prev" and page > 0:
        page -= 1

    await state.update_data(page=page)

    new_text = f"<b>Страница {page + 1}/{len(pages)}</b>\n\n{pages[page]}"
    new_markup = create_pagination_keyboard(user_id, page, state=BookState.reading)

    try:
        await callback.message.edit_text(
            new_text, reply_markup=new_markup, parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

    await callback.answer()


# -----------------------------
# MONTH STATISTICS
# -----------------------------
@router.callback_query(F.data.in_(LEXICON_MONTH.keys()))
async def choose_month_callback(callback: CallbackQuery):
    user_id = get_user_id(callback)
    month = callback.data

    res = get_stat_month(user_id, month)
    total = spend_month(user_id, month)

    await callback.message.edit_text(
        f"<u>Траты за <b>{LEXICON_MONTH[month]}</b>:</u>\n"
        f"{res}\n<b>ИТОГО: {total}</b> GEL"
    )

    await callback.message.answer("Показать подробно категорию ДРУГОЕ?")
    await callback.message.answer(month, reply_markup=another_kb(**LEXICON_ANOTHER))


@router.callback_query(F.data == "_another")
async def show_another(callback: CallbackQuery):
    user_id = get_user_id(callback)
    month = callback.message.text
    start_date, end_date = get_month_range(month)
    result = get_another(user_id, start_date, end_date)

    await callback.message.answer(
        f"<u>Другое за <b>{LEXICON_MONTH[month]}</b>:</u>\n{result}"
    )
    await callback.message.delete_reply_markup()


@router.callback_query(F.data == "_cancel")
async def cancel(callback: CallbackQuery):
    await callback.message.edit_text("Отмена")
    await callback.message.delete_reply_markup()
