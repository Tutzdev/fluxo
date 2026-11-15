from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from centavo.categories.schemas import CategorizationSummary
from centavo.month import check_month
from centavo.transactions.models import CategorySource

MAX_PAGE_SIZE = 100


class TransactionPath(BaseModel):
    transaction_id: int


class TransactionQuery(BaseModel):
    month: str | None = Field(default=None, description="YYYY-MM")
    account_id: int | None = None
    category_id: int | None = None
    needs_review: bool | None = Field(default=None, description="Only transactions without a category")
    search: str | None = Field(default=None, max_length=60)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=MAX_PAGE_SIZE)

    @field_validator("month")
    @classmethod
    def valid_month(cls, month: str | None) -> str | None:
        return check_month(month)


class CreateTransactionRequest(BaseModel):
    account_id: int
    occurred_on: date
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(max_digits=14, decimal_places=2, description="Negative for money going out")
    category_id: int | None = None

    @field_validator("amount")
    @classmethod
    def not_zero(cls, amount: Decimal) -> Decimal:
        if amount == 0:
            raise ValueError("must not be zero")

        return amount


class UpdateCategoryRequest(BaseModel):
    category_id: int | None = Field(description="null sends it back to review")


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    occurred_on: date
    description: str
    amount: Decimal
    category_id: int | None
    category_source: CategorySource | None
    category_confidence: Decimal | None
    needs_review: bool


class TransactionPageResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    income: Decimal = Field(description="Sum of positive amounts across every page")
    expenses: Decimal = Field(description="Sum of negative amounts across every page")


class RecategorizeResponse(BaseModel):
    recategorized: CategorizationSummary
