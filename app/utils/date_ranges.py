from datetime import datetime, timedelta
import calendar


def get_month_range(month: str, year: int | None = None) -> tuple:
    """Return the start and end datetimes for a month abbreviation."""
    now = datetime.now()
    month_cap = month[:1].upper() + month[1:].lower()

    if month_cap not in calendar.month_abbr:
        raise ValueError(f"Неверный месяц: {month}")

    desired_month = list(calendar.month_abbr).index(month_cap)
    desired_year = year or now.year

    if year is None and desired_month > now.month:
        desired_year -= 1

    start_date = datetime(desired_year, desired_month, 1)

    if desired_year == now.year and desired_month == now.month:
        end_date = now - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        last_day = calendar.monthrange(desired_year, desired_month)[1]
        end_date = datetime(desired_year, desired_month, last_day, 23, 59, 59)

    return start_date, end_date


def get_previous_n_month_ranges(
    month: str, n: int
) -> list[tuple[datetime, datetime]]:
    """Return date ranges for the previous n months before the selected month."""
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
        prev_year = selected_first_day.year
        prev_month = selected_first_day.month
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
    """Return the current week start date and current datetime."""
    current_datetime = datetime.now().replace(second=0, microsecond=0)
    start_of_week = (
        current_datetime - timedelta(days=current_datetime.weekday())
    ).date()
    return start_of_week, current_datetime
