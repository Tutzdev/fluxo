from decimal import Decimal

from flask_openapi3 import APIBlueprint, Tag

from fluxo.accounts.schemas import (
    AccountListResponse,
    AccountPath,
    AccountResponse,
    CreateAccountRequest,
    RenameAccountRequest,
)
from fluxo.accounts.service import AccountService, AccountView
from fluxo.auth.current import current_user_id, require_user
from fluxo.database import db_session
from fluxo.money import to_money
from fluxo.openapi import BEARER_SECURITY

blueprint = APIBlueprint(
    "accounts",
    __name__,
    url_prefix="/api/accounts",
    abp_tags=[Tag(name="Accounts", description="Bank accounts, cards and cash")],
    abp_security=BEARER_SECURITY,
)
blueprint.before_request(require_user)


def _service() -> AccountService:
    return AccountService(db_session())


@blueprint.get("", responses={200: AccountListResponse})
def list_accounts() -> dict[str, object]:
    views = _service().all(current_user_id())
    total = sum((view.balance for view in views), start=Decimal("0"))

    response = AccountListResponse(
        items=[_to_response(view) for view in views], total_balance=to_money(total)
    )
    return response.model_dump(mode="json")


@blueprint.post("", responses={201: AccountResponse})
def create_account(body: CreateAccountRequest) -> tuple[dict[str, object], int]:
    view = _service().create(current_user_id(), body.name, body.kind, body.opening_balance)
    return _to_response(view).model_dump(mode="json"), 201


@blueprint.patch("/<int:account_id>", responses={200: AccountResponse})
def rename_account(path: AccountPath, body: RenameAccountRequest) -> dict[str, object]:
    view = _service().rename(current_user_id(), path.account_id, body.name)
    return _to_response(view).model_dump(mode="json")


@blueprint.delete("/<int:account_id>", responses={204: None})
def delete_account(path: AccountPath) -> tuple[str, int]:
    _service().delete(current_user_id(), path.account_id)
    return "", 204


def _to_response(view: AccountView) -> AccountResponse:
    account = view.account

    return AccountResponse(
        id=account.id,
        name=account.name,
        kind=account.kind,
        opening_balance=account.opening_balance,
        balance=view.balance,
        transaction_count=view.transaction_count,
    )
