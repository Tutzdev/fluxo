from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from centavo.accounts.models import AccountKind


class AccountPath(BaseModel):
    account_id: int


class CreateAccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    kind: AccountKind
    opening_balance: Decimal = Field(default=Decimal("0.00"), max_digits=14, decimal_places=2)

    @field_validator("name")
    @classmethod
    def strip_name(cls, name: str) -> str:
        return name.strip()


class RenameAccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def strip_name(cls, name: str) -> str:
        return name.strip()


class AccountResponse(BaseModel):
    id: int
    name: str
    kind: AccountKind
    opening_balance: Decimal
    balance: Decimal
    transaction_count: int


class AccountListResponse(BaseModel):
    items: list[AccountResponse]
    total_balance: Decimal
