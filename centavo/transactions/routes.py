from flask_openapi3 import APIBlueprint, Tag

from centavo.auth.current import current_user_id, require_user
from centavo.categories.schemas import CategorizationSummary
from centavo.categorization.service import CategorizationService
from centavo.components import components
from centavo.database import db_session
from centavo.month import Month
from centavo.openapi import BEARER_SECURITY
from centavo.transactions.models import Transaction
from centavo.transactions.schemas import (
    CreateTransactionRequest,
    RecategorizeResponse,
    TransactionPageResponse,
    TransactionPath,
    TransactionQuery,
    TransactionResponse,
    UpdateCategoryRequest,
)
from centavo.transactions.service import NewTransaction, TransactionFilter, TransactionService

blueprint = APIBlueprint(
    "transactions",
    __name__,
    url_prefix="/api/transactions",
    abp_tags=[Tag(name="Transactions", description="Search, add, correct and re-categorize")],
    abp_security=BEARER_SECURITY,
)
blueprint.before_request(require_user)


def _service() -> TransactionService:
    session = db_session()
    return TransactionService(session, CategorizationService(session, components().classifier_cache))


@blueprint.get("", responses={200: TransactionPageResponse})
def search_transactions(query: TransactionQuery) -> dict[str, object]:
    filters = TransactionFilter(
        month=Month.parse(query.month) if query.month else None,
        account_id=query.account_id,
        category_id=query.category_id,
        needs_review=query.needs_review,
        search=query.search,
    )
    page = _service().search(current_user_id(), filters, query.page, query.page_size)

    response = TransactionPageResponse(
        items=[_to_response(item) for item in page.items],
        total=page.total,
        page=query.page,
        page_size=query.page_size,
        income=page.income,
        expenses=page.expenses,
    )
    return response.model_dump(mode="json")


@blueprint.post("", responses={201: TransactionResponse})
def create_transaction(body: CreateTransactionRequest) -> tuple[dict[str, object], int]:
    new = NewTransaction(
        account_id=body.account_id,
        occurred_on=body.occurred_on,
        description=body.description,
        amount=body.amount,
        category_id=body.category_id,
    )
    transaction = _service().create(current_user_id(), new)
    return _to_response(transaction).model_dump(mode="json"), 201


@blueprint.put("/<int:transaction_id>/category", responses={200: TransactionResponse})
def change_category(path: TransactionPath, body: UpdateCategoryRequest) -> dict[str, object]:
    transaction = _service().change_category(current_user_id(), path.transaction_id, body.category_id)
    return _to_response(transaction).model_dump(mode="json")


@blueprint.delete("/<int:transaction_id>", responses={204: None})
def delete_transaction(path: TransactionPath) -> tuple[str, int]:
    _service().delete(current_user_id(), path.transaction_id)
    return "", 204


@blueprint.post("/recategorize", responses={200: RecategorizeResponse})
def recategorize() -> dict[str, object]:
    result = _service().recategorize(current_user_id())

    summary = CategorizationSummary(
        by_rule=result.by_rule,
        by_model=result.by_model,
        left_for_review=result.left_for_review,
    )
    return RecategorizeResponse(recategorized=summary).model_dump(mode="json")


def _to_response(transaction: Transaction) -> TransactionResponse:
    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        occurred_on=transaction.occurred_on,
        description=transaction.description,
        amount=transaction.amount,
        category_id=transaction.category_id,
        category_source=transaction.category_source,
        category_confidence=transaction.category_confidence,
        needs_review=transaction.needs_review,
    )
