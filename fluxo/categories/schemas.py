from pydantic import BaseModel, Field, field_validator

from fluxo.categories.models import CategoryKind

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


class CategoryPath(BaseModel):
    category_id: int


class RulePath(BaseModel):
    rule_id: int


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    kind: CategoryKind
    color: str = Field(pattern=HEX_COLOR)

    @field_validator("name")
    @classmethod
    def strip_name(cls, name: str) -> str:
        return name.strip()


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    color: str | None = Field(default=None, pattern=HEX_COLOR)


class CreateRuleRequest(BaseModel):
    pattern: str = Field(
        min_length=2, max_length=60, description="Text the description must contain, e.g. 'IFOOD'"
    )


class RuleResponse(BaseModel):
    id: int
    pattern: str


class CategoryResponse(BaseModel):
    id: int
    name: str
    kind: CategoryKind
    color: str
    rules: list[RuleResponse]


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]


class CategorizationSummary(BaseModel):
    by_rule: int
    by_model: int
    left_for_review: int


class CreateRuleResponse(BaseModel):
    rule: RuleResponse
    recategorized: CategorizationSummary
