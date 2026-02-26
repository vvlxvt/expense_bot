from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.lexicon.lexicon import LEXICON_book
from app.services import books


def create_pagination_keyboard(page=1) -> InlineKeyboardMarkup:
    if books.keys():
        max_key = max(books, key=lambda k: len(books[k]))
        book = books[max_key]
        middle_text = f"{page}/{len(book)} CLOSE"
        kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

        buttons: list[InlineKeyboardButton] = []

        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text=LEXICON_book.get("backward", "<<"),
                    callback_data="backward",
                )
            )

        buttons.append(
            InlineKeyboardButton(
                text=middle_text,
                callback_data="close",
            )
        )

        if page < len(book):
            buttons.append(
                InlineKeyboardButton(
                    text=LEXICON_book.get("forward", ">>"),
                    callback_data="forward",
                )
            )

        kb_builder.row(*buttons)

    # Добавляем дополнительную кнопку в новый ряд
    extra_button = InlineKeyboardButton(text="Сгруппировать?", callback_data="group")
    kb_builder.row(extra_button)
    return kb_builder.as_markup()
