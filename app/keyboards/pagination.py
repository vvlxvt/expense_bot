from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon import LEXICON_book
from services import books


def create_pagination_keyboard(page=1) -> InlineKeyboardMarkup:
    if books.keys():
        max_key = max(books, key=lambda k: len(books[k]))
        book = books[max_key]
        middle_button = f"{page}/{len(book)} CLOSE"
        buttons = ["backward", middle_button, "forward"]
        if page == 1:
            buttons = buttons[1:]
        elif page == len(book):
            buttons = buttons[:-1]
        kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    button_list = [
        InlineKeyboardButton(
            text=LEXICON_book.get(button, button), callback_data=button
        )
        for button in buttons
    ]
    kb_builder.row(*button_list)

    # Добавляем дополнительную кнопку в новый ряд
    extra_button = InlineKeyboardButton(text="Сгруппировать?", callback_data="group")
    kb_builder.row(extra_button)
    return kb_builder.as_markup()
