from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def add_subname_kb(**kwargs: dict[str, str]) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    for button, text in kwargs.items():
        buttons.append(InlineKeyboardButton(text=text, callback_data=button))
    # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=2)
    # kb_builder.row(InlineKeyboardButton(text=LEXICON_CORRECT['correct'], callback_data='correct'),width=1)
    return kb_builder.as_markup()


def another_kb(**kwargs: dict[str, str]) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    for button, text in kwargs.items():
        buttons.append(InlineKeyboardButton(text=text, callback_data=button))

        # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=2)

    return kb_builder.as_markup()

def one_button_kb(text: str, url: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    # Добавляем одну кнопку с URL
    kb_builder.row(InlineKeyboardButton(text=text,url=url))
    return kb_builder.as_markup()
