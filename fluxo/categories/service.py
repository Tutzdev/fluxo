from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fluxo.categories.models import Category, CategoryKind, CategoryRule
from fluxo.categorization.service import CategorizationResult, CategorizationService
from fluxo.errors import ConflictError, InvalidInputError
from fluxo.ownership import get_owned
from fluxo.text import normalize_description


@dataclass(frozen=True, slots=True)
class CategoryView:
    category: Category
    rules: list[CategoryRule]


class CategoryService:
    def __init__(self, session: Session, categorization: CategorizationService) -> None:
        self._session = session
        self._categorization = categorization

    def all(self, user_id: int) -> list[CategoryView]:
        categories = self._session.scalars(
            select(Category).where(Category.user_id == user_id).order_by(Category.kind, Category.name)
        ).all()
        rules = self._session.scalars(
            select(CategoryRule).where(CategoryRule.user_id == user_id).order_by(CategoryRule.pattern)
        ).all()

        rules_by_category: dict[int, list[CategoryRule]] = defaultdict(list)

        for rule in rules:
            rules_by_category[rule.category_id].append(rule)

        return [CategoryView(category, rules_by_category[category.id]) for category in categories]

    def get(self, user_id: int, category_id: int) -> CategoryView:
        category = get_owned(self._session, Category, category_id, user_id)
        rules = self._session.scalars(
            select(CategoryRule).where(CategoryRule.category_id == category_id).order_by(CategoryRule.pattern)
        ).all()

        return CategoryView(category, list(rules))

    def create(self, user_id: int, name: str, kind: CategoryKind, color: str) -> Category:
        category = Category(user_id=user_id, name=name, kind=kind, color=color)
        self._session.add(category)

        self._flush_unique_name()
        self._session.commit()
        return category

    def update(self, user_id: int, category_id: int, name: str | None, color: str | None) -> CategoryView:
        category = get_owned(self._session, Category, category_id, user_id)

        if name is not None:
            category.name = name.strip()

        if color is not None:
            category.color = color

        self._flush_unique_name()
        self._session.commit()
        return self.get(user_id, category_id)

    def delete(self, user_id: int, category_id: int) -> None:
        """Its transactions go back to "needs review"; its rules and budget go with it."""
        category = get_owned(self._session, Category, category_id, user_id)

        self._session.delete(category)
        self._categorization.labels_changed(user_id)
        self._session.commit()

    def add_rule(
        self, user_id: int, category_id: int, pattern: str
    ) -> tuple[CategoryRule, CategorizationResult]:
        """Saves the rule and applies it right away to everything not categorized by hand."""
        get_owned(self._session, Category, category_id, user_id)
        normalized = normalize_description(pattern)

        if not normalized:
            raise InvalidInputError("INVALID_PATTERN", "A rule needs at least one word with letters.")

        rule = CategoryRule(user_id=user_id, category_id=category_id, pattern=normalized)
        self._session.add(rule)

        try:
            self._session.flush()
        except IntegrityError as error:
            self._session.rollback()
            raise ConflictError("RULE_EXISTS", f"There is already a rule for '{normalized}'.") from error

        self._categorization.labels_changed(user_id)
        result = self._categorization.recategorize_all(user_id)

        self._session.commit()
        return rule, result

    def delete_rule(self, user_id: int, rule_id: int) -> None:
        """Transactions it categorized keep their category until the next re-categorization."""
        rule = get_owned(self._session, CategoryRule, rule_id, user_id)

        self._session.delete(rule)
        self._categorization.labels_changed(user_id)
        self._session.commit()

    def _flush_unique_name(self) -> None:
        try:
            self._session.flush()
        except IntegrityError as error:
            self._session.rollback()
            raise ConflictError(
                "CATEGORY_NAME_TAKEN", "You already have a category with this name."
            ) from error
