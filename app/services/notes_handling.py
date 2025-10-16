import re
from aiogram.types import CallbackQuery
from datetime import datetime
from database import no_subs, Queue, Expense, get_subname, add_new_data
from lexicon import find_value, LEXICON_CHOICE


def make_name_price(note: str) -> tuple:
    # парсит сообщение с тратой на товар и цену, возвращает кортеж (товар, цена)
    pattern_1 = r"(^.+)\s(\d{0,3}[\.|,]?\d{1,2}$)"
    pattern_2 = r"(^\d{0,3}[\.|,]?\d{1,2})\s(.+$)"
    res_1 = re.match(pattern_1, note)
    res_2 = re.match(pattern_2, note)
    if isinstance(res_1, re.Match):
        return res_1[1], res_1[2]
    elif isinstance(res_2, re.Match):
        return res_2[2], res_2[1]
    else:
        return note, 0


def split_expense(message: str) -> list[str]:
    # если сообщение многострочное, преобразует сообщение в список строк
    res = []
    if "\n" in message:
        return message.split("\n")
    else:
        res.append(message)
        return res


def comma_replace(num: str) -> str:
    if "," in num:
        num = num.replace(",", ".")
    return num


def make_expense(message: str, user_id: int) -> Expense:
    # преообразует строчку с тратой в обьект Expense
    name, price = make_name_price(message)
    name = name.lower()
    price = comma_replace(price)
    today = datetime.now().replace(second=0, microsecond=0)
    if "зефир" in name:
        cat = "зефир"
    else:
        cat = get_subname(name)
        if cat:
            cat = cat[0]
    return Expense(name, cat, price, today, message, user_id, False)


def get_categories(row_messages: str, user_id: int) -> str:
    # получаю сырое сообщение, распаршенные наименования добавляю в базу данных, вывожу их категории
    messages = split_expense(row_messages)
    # получаю список строк из сообщения
    all_subnames = []
    # создаю пустой список категорий
    for message in messages:
        try:
            expense = make_expense(message, user_id)
            if expense.subname != None:
                add_new_data(expense)
                all_subnames.append(expense.subname)
            else:
                # добавляю в очередь товаров без категории
                no_subs.queue(
                    (expense.name, expense.price, expense.raw),
                )
        except TypeError as e:
            all_subnames.append("без категории")
            # если сообщение не парсится оно просто записывается в столбец "сырых сообщений" raw
            today = datetime.now().replace(second=0, microsecond=0)
            expense = Expense(
                "без категории", "без категории", 0, today, message, user_id, False
            )
            add_new_data(expense)
            print(f"{e} не понимаю")
    return ", ".join(all_subnames)


def form_expense_instance(no_subs: Queue, callback: CallbackQuery) -> Expense:
    """преобразует траты без категории в класс Expense"""
    name = no_subs.peek()[0]
    sub_name = find_value(LEXICON_CHOICE, callback.data)
    price = no_subs.peek()[1]
    today = datetime.now().replace(second=0, microsecond=0)
    raw_message = no_subs.peek()[2]
    user_id = callback.from_user.id
    flag = True
    return Expense(name, sub_name, price, today, raw_message, user_id, flag)


# @dp.message_handler(commands=['remove_keyboard'])
# async def remove_keyboard(message: types.Message):
#     # Удаляем клавиатуру с предыдущего сообщения методом delete_message
#     await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
#     await message.answer("Клавиатура удалена")
#
#
# @dp.message_handler(commands=['edit_reply_markup'])
# async def edit_reply_markup(message: types.Message):
#     # Изменяем клавиатуру с предыдущего сообщения методом edit_message_reply_markup
#     await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id - 1, reply_markup=None)
#     await message.answer("Клавиатура удалена")
