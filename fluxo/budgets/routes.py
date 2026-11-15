from flask_openapi3 import APIBlueprint, Tag

from fluxo.auth.current import current_user_id, require_user
from fluxo.budgets.schemas import (
    BudgetListResponse,
    BudgetPath,
    BudgetQuery,
    BudgetResponse,
    SetBudgetRequest,
)
from fluxo.budgets.service import BudgetProgress, BudgetService
from fluxo.components import components
from fluxo.database import db_session
from fluxo.month import Month
from fluxo.openapi import BEARER_SECURITY

blueprint = APIBlueprint(
    "budgets",
    __name__,
    url_prefix="/api/budgets",
    abp_tags=[Tag(name="Budgets", description="Monthly limits per expense category")],
    abp_security=BEARER_SECURITY,
)
blueprint.before_request(require_user)


@blueprint.get("", responses={200: BudgetListResponse})
def list_budgets(query: BudgetQuery) -> dict[str, object]:
    month = Month.parse(query.month) if query.month else Month.of(components().clock.today())
    progress = BudgetService(db_session()).progress(current_user_id(), month)

    response = BudgetListResponse(month=str(month), items=[_to_response(item) for item in progress])
    return response.model_dump(mode="json")


@blueprint.put("/<int:category_id>", responses={204: None})
def set_budget(path: BudgetPath, body: SetBudgetRequest) -> tuple[str, int]:
    BudgetService(db_session()).set_limit(current_user_id(), path.category_id, body.monthly_limit)
    return "", 204


@blueprint.delete("/<int:category_id>", responses={204: None})
def remove_budget(path: BudgetPath) -> tuple[str, int]:
    BudgetService(db_session()).remove(current_user_id(), path.category_id)
    return "", 204


def _to_response(progress: BudgetProgress) -> BudgetResponse:
    return BudgetResponse(
        category_id=progress.category.id,
        category_name=progress.category.name,
        color=progress.category.color,
        monthly_limit=progress.monthly_limit,
        spent=progress.spent,
        remaining=progress.remaining,
        percent_used=progress.percent_used,
        status=progress.status,
    )
