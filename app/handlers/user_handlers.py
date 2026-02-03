from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from app.keyboards.pagination import create_pagination_keyboard
from app.lexicon import LEXICON, LEXICON_MONTH, LEXICON_ANOTHER
from app.keyboards import add_subname_kb, another_kb, one_button_kb
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
)
from app.filters import IsAdmin
from app.services import prepare_book, get_month_range, books
from app.config.config import GlobalVars
from app import config

# Build charts URL from environment
_conf = config.load_config(None)
_BASE_WEBHOOK_URL = _conf.base_webhook_url.rstrip("/") if _conf.base_webhook_url else ""
_CHARTS_URL = f"{_BASE_WEBHOOK_URL}/stats" if _BASE_WEBHOOK_URL else "/stats"


router: Router = Router()
router.message.filter(IsAdmin(_conf.tg_bot.admin_ids))


@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(LEXICON[message.text])


@router.message(Command(commands="help"))
async def process_help_command(message: Message):
    await message.answer(LEXICON[message.text])


@router.message(Command(commands="tanya"))
async def process_help_command(message: Message):
    user_id = 1194999116
    result = get_my_expenses(user_id)
    prepare_book(result, user_id)
    page = max(books[user_id])
    text = "Последние траты Тани в этом месяце: "
    await message.answer(text=f" <b>{text}</b>\n {books[user_id][page]} ")


@router.message(Command(commands="del_last_note"),)
async def del_note(message: Message):
    last = del_last_note()
    text = "удалена запись: "
    await message.answer(text=text + last)


@router.message(Command(commands="today"))
async def get_today(message: Message):
    message_date = message.date
    user_id = message.from_user.id
    total_spending = spend_today(user_id)
    date_format = "%d-%m-%Y"  # Формат часов:минут:секунд
    formatted_time = message_date.strftime(date_format)
    await message.answer(
        text=f"сегодня <i>{formatted_time}</i> я потратил/а <b>{total_spending}</b> GEL "
    )


@router.message(Command(commands="week"))
async def get_week(message: Message):
    user_id = message.from_user.id
    res = get_stat_week(user_id)
    total = round(spend_week(user_id), 2)
    await message.answer(
        text=f"  <b>{res}</b>\n С начала недели мною потрачено: {total} GEL "
    )


@router.message(Command(commands="month"))
async def get_month(message: Message):
    text = "За какой месяц показать статистику?"
    await message.answer(text=text, reply_markup=add_subname_kb(**LEXICON_MONTH))


@router.message(Command(commands="charts"))
async def charts_command(message: Message):
    keyboard = one_button_kb("Открыть график", _CHARTS_URL)
    await message.answer("Перейдите по ссылке:", reply_markup=keyboard)


@router.message(Command(commands="my_month"))
async def get_month(message: Message):
    user_id = message.from_user.id
    result = get_my_expenses(user_id)
    prepare_book(result, user_id)
    print(books)
    gv = GlobalVars(user_id)
    gv.page = 1
    text = "Все мои траты с начала месяца: "
    await message.answer(
        text=f" <b>{text}</b>\n {books[user_id][gv.page]} ",
        reply_markup=create_pagination_keyboard(),
    )


@router.callback_query(F.data.in_(LEXICON_MONTH.keys()))
async def process_chose_month(callback: CallbackQuery):
    month = callback.data
    res = get_stat_month(month)
    total = spend_month(month)
    name_month = LEXICON_MONTH[callback.data]
    await callback.message.edit_text(
        text=f"<u>Траты за <b>{name_month}</b>:</u> \n{res}\n<b> ИТОГО: {total}</b> gel"
    )
    await callback.message.answer(text=f"Показать подробно категорию ДРУГОЕ?")
    await callback.message.answer(
        text=month, reply_markup=another_kb(**LEXICON_ANOTHER)
    )


@router.callback_query(F.data == "group")
async def show_another(callback: CallbackQuery):
    user_id = callback.from_user.id
    result = get_my_expenses_group(user_id)
    await callback.message.answer(
        text=f"<u>Мои траты за текущий месяц:</u> \n{result}\n"
    )
    # await callback.message.delete_reply_markup()


@router.callback_query(F.data == "_another")
async def show_another(callback: CallbackQuery):
    month = callback.message.text
    start_date, end_date = get_month_range(month)
    result = get_another(start_date, end_date)
    await callback.message.answer(
        text=f"<u>Другое за <b>{LEXICON_MONTH[month]}</b>:</u> \n{result}\n"
    )
    await callback.message.delete_reply_markup()


@router.callback_query(F.data == "_cancel")
async def cancel_add_expense(callback: CallbackQuery):
    await callback.message.edit_text(text="отмена")
    await callback.message.delete_reply_markup()

