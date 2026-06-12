from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def add_subname_kb(**kwargs: dict[str, str]) -> InlineKeyboardMarkup:
    """Build an inline keyboard from callback-data keys and button labels."""
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    for button, text in kwargs.items():
        buttons.append(InlineKeyboardButton(text=text, callback_data=button))
    # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=2)
    # kb_builder.row(InlineKeyboardButton(text=LEXICON_CORRECT['correct'], callback_data='correct'),width=1)
    return kb_builder.as_markup()


def category_choice_kb(
    ml_category: str | None,
    fuzzy_category: str | None,
) -> InlineKeyboardMarkup:
    """Build category suggestion buttons plus manual and cancel actions."""
    kb_builder = InlineKeyboardBuilder()

    if ml_category:
        kb_builder.row(
            InlineKeyboardButton(
                text=f"ML: {ml_category}",
                callback_data="choice:ml",
            )
        )

    if fuzzy_category:
        kb_builder.row(
            InlineKeyboardButton(
                text=f"Fuzzy: {fuzzy_category}",
                callback_data="choice:fuzzy",
            )
        )

    kb_builder.row(
        InlineKeyboardButton(text="Выбрать вручную", callback_data="manual_category")
    )
    kb_builder.row(InlineKeyboardButton(text="ОТМЕНИТЬ", callback_data="cancel"))

    return kb_builder.as_markup()


def another_kb(**kwargs: dict[str, str]) -> InlineKeyboardMarkup:
    """Build a generic two-column inline keyboard from a label mapping."""
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    for button, text in kwargs.items():
        buttons.append(InlineKeyboardButton(text=text, callback_data=button))

        # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=2)

    return kb_builder.as_markup()

def one_button_kb(text: str, url: str) -> InlineKeyboardMarkup:
    """Build a one-button URL keyboard."""
    kb_builder = InlineKeyboardBuilder()
    # Добавляем одну кнопку с URL
    kb_builder.row(InlineKeyboardButton(text=text,url=url))
    return kb_builder.as_markup()
