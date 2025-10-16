from dataclasses import dataclass
from datetime import datetime


@dataclass
class Expense:
    name: str | None
    subname: str | None
    price: str | float | None
    today: datetime | None
    raw: str
    user_id: str | int | None
    flag: bool | None
    # флаг указывает добавлять ли новую категорию в словарь

    def __repr__(self):
        return f"{self.__sizeof__()}"
