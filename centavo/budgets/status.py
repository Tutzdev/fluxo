"""How a budget is doing, as a pure function of limit and spending."""

import enum
from decimal import Decimal

WARNING_THRESHOLD = Decimal("0.80")


class BudgetStatus(enum.StrEnum):
    ON_TRACK = "on_track"
    WARNING = "warning"
    EXCEEDED = "exceeded"


def budget_status(monthly_limit: Decimal, spent: Decimal) -> BudgetStatus:
    if spent > monthly_limit:
        return BudgetStatus.EXCEEDED

    if spent >= monthly_limit * WARNING_THRESHOLD:
        return BudgetStatus.WARNING

    return BudgetStatus.ON_TRACK
