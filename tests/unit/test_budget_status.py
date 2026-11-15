from decimal import Decimal

import pytest

from centavo.budgets.status import BudgetStatus, budget_status


@pytest.mark.parametrize(
    ("spent", "expected"),
    [
        ("0", BudgetStatus.ON_TRACK),
        ("799.99", BudgetStatus.ON_TRACK),
        ("800", BudgetStatus.WARNING),
        ("1000", BudgetStatus.WARNING),
        ("1000.01", BudgetStatus.EXCEEDED),
    ],
)
def test_warns_from_eighty_percent_and_flags_only_what_goes_over_the_limit(spent, expected):
    assert budget_status(Decimal("1000"), Decimal(spent)) is expected
