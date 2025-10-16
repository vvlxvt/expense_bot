import asyncio
from datetime import datetime, timedelta
import calendar

books = {}


async def daily_timer():
    while True:
        now = datetime.now()
        next_run = datetime(now.year, now.month, now.day) + timedelta(days=1)
        sleep_seconds = (next_run - now).total_seconds()
        # Ожидаем до следующего 00:00
        await asyncio.sleep(sleep_seconds)
        books.clear()


def get_month_range(month: str) -> tuple:
    desired_year = datetime.now().year
    desired_month = list(calendar.month_abbr).index(month.capitalize())
    current_month = datetime.now().month
    if current_month < desired_month:
        desired_year -= 1
    start_date = datetime(desired_year, desired_month, 1)
    if desired_month == 12:
        end_date = start_date.replace(year=desired_year, month=12, day=31)
    else:
        end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(
            minutes=1
        )
    print(start_date, end_date)
    return start_date, end_date


def get_week_range() -> tuple:
    current_datetime = datetime.now().replace(second=0, microsecond=0)
    # Вычисляем начало текущей недели
    start_of_week = (
        current_datetime - timedelta(days=current_datetime.weekday())
    ).date()
    return start_of_week, current_datetime


def _get_part_text(expenses_out: str, start: int, page_size: int) -> tuple[str, int]:
    end = start + page_size
    nums = list(range(start + 1, end + 1))  # постраничная нумерация
    exps = [x + " " + str(y) for x, y in expenses_out[start:end]]
    nums_exps = list(zip(nums, exps))
    result = [str(x) + ".  " + y for x, y in nums_exps]
    print(result)
    return "\n".join(result)


def prepare_book(text: list, user_id: int) -> None:
    if id not in books:
        books[user_id] = {}
    finish = len(text) - 1
    start, i = 0, 1
    page_size = 20
    while start < finish:
        strokes = _get_part_text(text, start, page_size)
        books[user_id].update({i: strokes})
        start += page_size
        i += 1
