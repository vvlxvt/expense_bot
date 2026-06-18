from collections import defaultdict
from time import time

START_TIME = time()
_counters: dict[str, int] = defaultdict(int)


def inc(metric: str, amount: int = 1) -> None:
    """Increase an in-memory counter by the given amount."""
    _counters[metric] += amount


def set_metric(metric: str, value: int) -> None:
    """Set an in-memory metric to an explicit integer value."""
    _counters[metric] = value


def render_prometheus() -> str:
    """Render all in-memory metrics in Prometheus text exposition format."""
    lines = [
        "# HELP expensebot_uptime_seconds Seconds since the bot process started.",
        "# TYPE expensebot_uptime_seconds gauge",
        f"expensebot_uptime_seconds {int(time() - START_TIME)}",
    ]

    for name in sorted(_counters):
        lines.extend(
            [
                f"# TYPE expensebot_{name} counter",
                f"expensebot_{name} {_counters[name]}",
            ]
        )

    return "\n".join(lines) + "\n"
