from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from centavo.month import check_month


class MonthQuery(BaseModel):
    month: str | None = Field(default=None, description="YYYY-MM, defaults to the current month")

    @field_validator("month")
    @classmethod
    def valid_month(cls, month: str | None) -> str | None:
        return check_month(month)


class TrendQuery(MonthQuery):
    months: int = Field(default=6, ge=1, le=24)


class CategorySpendingResponse(BaseModel):
    category_id: int | None
    name: str
    color: str
    amount: Decimal


class SummaryResponse(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal
    needs_review: int
    by_category: list[CategorySpendingResponse]


class MonthTotalsResponse(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal


class TrendResponse(BaseModel):
    items: list[MonthTotalsResponse]


class UpcomingResponse(BaseModel):
    description: str
    amount: Decimal
    expected_day: int
    category_id: int | None
    months_seen: int


class ForecastResponse(BaseModel):
    today: date
    days_left: int
    balance_now: Decimal
    expected_income: Decimal
    expected_bills: Decimal
    projected_day_to_day: Decimal
    projected_end_balance: Decimal
    upcoming: list[UpcomingResponse]
