from aiogram.filters import BaseFilter
from aiogram.types import Message
from typing import Iterable


# Собственный фильтр, проверяющий на админа
class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: Iterable[int]) -> None:
        """Store the allowed Telegram user IDs for fast membership checks."""
        # Приводим к set для быстрого поиска и избегаем ошибок
        self.admin_ids = set(admin_ids)

    async def __call__(self, message: Message) -> bool:
        """Allow a message only when it was sent by an configured admin user."""
        user = message.from_user
        return user is not None and user.id in self.admin_ids


