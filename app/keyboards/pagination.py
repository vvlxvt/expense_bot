from app.config import BookState
from app.services import books


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_pagination_keyboard(
    user_id: int, page: int, state: str
) -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру для пагинации.

    Для BookState.reading: кнопки prev/next/close и "Сгруппировать?"
    Для BookState.grouped: только кнопка close
    """
    kb = InlineKeyboardBuilder()

    if state == BookState.reading:
        user_pages = books.get(user_id, [])
        total = len(user_pages)

        buttons = []
        if page > 0:
            buttons.append(InlineKeyboardButton(text="◀", callback_data="prev"))
        buttons.append(
            InlineKeyboardButton(text=f"{page + 1}/{total}", callback_data="close")
        )
        if page < total - 1:
            buttons.append(InlineKeyboardButton(text="▶", callback_data="next"))

        if buttons:
            kb.row(*buttons)

        # Кнопка для grouped
        kb.row(InlineKeyboardButton(text="Сгруппировать?", callback_data="group"))

    elif state == BookState.grouped:
        # Для grouped оставляем только закрытие
        kb.row(InlineKeyboardButton(text="Закрыть", callback_data="close"))

    return kb.as_markup()
