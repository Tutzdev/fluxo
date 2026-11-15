from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from fluxo.budgets.status import BudgetStatus
from fluxo.month import check_month


class BudgetPath(BaseModel):
    category_id: int


class BudgetQuery(BaseModel):
    month: str | None = Field(default=None, description="YYYY-MM, defaults to the current month")

    @field_validator("month")
    @classmethod
    def valid_month(cls, month: str | None) -> str | None:
        return check_month(month)


class SetBudgetRequest(BaseModel):
    monthly_limit: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class BudgetResponse(BaseModel):
    category_id: int
    category_name: str
    color: str
    monthly_limit: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: int
    status: BudgetStatus


class BudgetListResponse(BaseModel):
    month: str
    items: list[BudgetResponse]
