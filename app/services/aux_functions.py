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
import calendar


def get_month_range(month: str) -> tuple:
    """
    Возвращает кортеж (start_date, end_date)
    """
    now = datetime.now()
    # Приводим к первому символу заглавному, остальное строчные, чтобы совпадало с calendar.month_abbr
    month_cap = month[:1].upper() + month[1:].lower()

    if month_cap not in calendar.month_abbr:
        raise ValueError(f"Неверный месяц: {month}")

    desired_month = list(calendar.month_abbr).index(month_cap)
    desired_year = now.year

    # Если выбран месяц позже текущего — берём прошлый год
    if desired_month > now.month:
        desired_year -= 1

    start_date = datetime(desired_year, desired_month, 1)

    # Если выбран текущий месяц — конец = вчерашний день
    if desired_month == now.month:
        end_date = now - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        # Для других месяцев — конец = последний день месяца
        last_day = calendar.monthrange(desired_year, desired_month)[1]
        end_date = datetime(desired_year, desired_month, last_day, 23, 59, 59)

    return start_date, end_date


def get_previous_n_month_ranges(month: str, n: int) -> list[tuple[datetime, datetime]]:
    """
    month: сокращённое название месяца на английском, например 'jan', 'Feb', 'OCT'
    Возвращает список кортежей (start_date, end_date) для предыдущих n месяцев
    относительно выбранного месяца (не включая сам выбранный месяц).
    """
    now = datetime.now()
    month_cap = month[:1].upper() + month[1:].lower()

    if month_cap not in calendar.month_abbr:
        raise ValueError(f"Неверный месяц: {month}")

    desired_month = list(calendar.month_abbr).index(month_cap)
    desired_year = now.year

    if desired_month > now.month:
        desired_year -= 1

    selected_first_day = datetime(desired_year, desired_month, 1)

    ranges: list[tuple[datetime, datetime]] = []
    for i in range(1, n + 1):
        prev = selected_first_day - timedelta(days=1)
        # отматываем помесячно i раз от первого дня выбранного месяца
        prev_year = selected_first_day.year
        prev_month = selected_first_day.month
        # вычислим i-й предыдущий месяц через календарь
        # простой цикл по месяцам назад
        steps = i
        y, m = prev_year, prev_month
        while steps > 0:
            m -= 1
            if m == 0:
                m = 12
                y -= 1
            steps -= 1
        start_date = datetime(y, m, 1)
        last_day = calendar.monthrange(y, m)[1]
        end_date = datetime(y, m, last_day, 23, 59, 59)
        ranges.append((start_date, end_date))

    return ranges


def get_week_range() -> tuple:
    current_datetime = datetime.now().replace(second=0, microsecond=0)
    # Вычисляем начало текущей недели
    start_of_week = (
        current_datetime - timedelta(days=current_datetime.weekday())
    ).date()
    return start_of_week, current_datetime


from collections import defaultdict

# Хранилище страниц по пользователю
books: dict[int, dict[int, str]] = defaultdict(dict)


def _get_part_text(expenses_out: list[tuple], start: int, page_size: int) -> str:
    print(expenses_out)
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
