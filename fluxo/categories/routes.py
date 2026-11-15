from flask_openapi3 import APIBlueprint, Tag

from fluxo.auth.current import current_user_id, require_user
from fluxo.categories.models import Category, CategoryRule
from fluxo.categories.schemas import (
    CategorizationSummary,
    CategoryListResponse,
    CategoryPath,
    CategoryResponse,
    CreateCategoryRequest,
    CreateRuleRequest,
    CreateRuleResponse,
    RulePath,
    RuleResponse,
    UpdateCategoryRequest,
)
from fluxo.categories.service import CategoryService, CategoryView
from fluxo.categorization.service import CategorizationService
from fluxo.components import components
from fluxo.database import db_session
from fluxo.openapi import BEARER_SECURITY

blueprint = APIBlueprint(
    "categories",
    __name__,
    url_prefix="/api/categories",
    abp_tags=[Tag(name="Categories", description="Categories and the keyword rules that fill them")],
    abp_security=BEARER_SECURITY,
)
blueprint.before_request(require_user)


def _service() -> CategoryService:
    session = db_session()
    return CategoryService(session, CategorizationService(session, components().classifier_cache))


@blueprint.get("", responses={200: CategoryListResponse})
def list_categories() -> dict[str, object]:
    views = _service().all(current_user_id())
    return CategoryListResponse(items=[_to_response(view) for view in views]).model_dump(mode="json")


@blueprint.post("", responses={201: CategoryResponse})
def create_category(body: CreateCategoryRequest) -> tuple[dict[str, object], int]:
    category = _service().create(current_user_id(), body.name, body.kind, body.color)
    return _to_response(CategoryView(category, rules=[])).model_dump(mode="json"), 201


@blueprint.patch("/<int:category_id>", responses={200: CategoryResponse})
def update_category(path: CategoryPath, body: UpdateCategoryRequest) -> dict[str, object]:
    view = _service().update(current_user_id(), path.category_id, body.name, body.color)
    return _to_response(view).model_dump(mode="json")


@blueprint.delete("/<int:category_id>", responses={204: None})
def delete_category(path: CategoryPath) -> tuple[str, int]:
    _service().delete(current_user_id(), path.category_id)
    return "", 204


@blueprint.post("/<int:category_id>/rules", responses={201: CreateRuleResponse})
def add_rule(path: CategoryPath, body: CreateRuleRequest) -> tuple[dict[str, object], int]:
    rule, result = _service().add_rule(current_user_id(), path.category_id, body.pattern)

    response = CreateRuleResponse(
        rule=_rule_response(rule),
        recategorized=CategorizationSummary(
            by_rule=result.by_rule,
            by_model=result.by_model,
            left_for_review=result.left_for_review,
        ),
    )
    return response.model_dump(mode="json"), 201


@blueprint.delete("/rules/<int:rule_id>", responses={204: None})
def delete_rule(path: RulePath) -> tuple[str, int]:
    _service().delete_rule(current_user_id(), path.rule_id)
    return "", 204


def _to_response(view: CategoryView) -> CategoryResponse:
    category: Category = view.category

    return CategoryResponse(
        id=category.id,
        name=category.name,
        kind=category.kind,
        color=category.color,
        rules=[_rule_response(rule) for rule in view.rules],
    )


def _rule_response(rule: CategoryRule) -> RuleResponse:
    return RuleResponse(id=rule.id, pattern=rule.pattern)
