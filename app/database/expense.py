from dataclasses import dataclass
from datetime import datetime


@dataclass
class Expense:
    # ОБЯЗАТЕЛЬНЫЕ ПОЛЯ
    raw: str
    user_id: int
    # НЕОБЯЗАТЕЛЬНЫЕ ПОЛЯ
    item: str | None = None
    price: float | None = 0.0
    category: str | None = None
    created: datetime | None = None
    item_id: int | None = None
    flag: bool = False

    def __repr__(self):
        """Return a compact debug representation of an expense."""
        return f"Expense(item={self.item}, price={self.price}, category={self.category}, flag={self.flag})"
