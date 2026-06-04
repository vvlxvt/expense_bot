import asyncio


async def daily_timer():
    while True:
        now = datetime.now()
        next_run = datetime(now.year, now.month, now.day) + timedelta(days=1)
        sleep_seconds = (next_run - now).total_seconds()
        # Ожидаем до следующего 00:00
        await asyncio.sleep(sleep_seconds)
        books.clear()


from datetime import datetime, timedelta

from app.utils.date_ranges import (
    get_month_range,
    get_week_range,
    get_previous_n_month_ranges,
)


from collections import defaultdict

# Хранилище страниц по пользователю
books: dict[int, dict[int, str]] = defaultdict(dict)


def _get_part_text(expenses_out: list[tuple], start: int, page_size: int) -> str:
    part = expenses_out[start : start + page_size]

    lines = []
    for idx, item in enumerate(part, start=start + 1):
        # проверяем, что элемент кортеж из двух значений
        if isinstance(item, (list, tuple)) and len(item) == 2:
            name, amount = item
            lines.append(f"{idx}. {name} — {amount}")
        else:
            # если вдруг элемент не кортеж, просто выводим как есть
            lines.append(f"{idx}. {item}")
    return "\n".join(lines)


def prepare_book(expenses_out: list[tuple], user_id: int, page_size: int = 20):
    """
    Создаёт словарь страниц для пользователя
    books[user_id] = {0: 'страница 1', 1: 'страница 2', ...}
    """
    global books
    from collections import defaultdict

    if "books" not in globals():
        books = defaultdict(dict)

    books[user_id].clear()

    start = 0
    page = 0
    print(expenses_out)
    while start < len(expenses_out):
        books[user_id][page] = _get_part_text(expenses_out, start, page_size)
        start += page_size
        page += 1


"""
if __name__ == "__main__":
    expenses_out = ["анализы...... 37.5", "макдак уле... 35", "итого:....... 72.5"]
    user_id = 1194999116
    page_size = 20
    prepare_book(expenses_out, user_id, page_size)
    print(books)
"""
