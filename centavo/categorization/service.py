"""Decides a category for transactions nobody categorized by hand.

Order of trust:
  1. a rule the user wrote          -> category_source = rule
  2. the model, if it is sure       -> category_source = model
  3. otherwise leave it empty       -> shows up in "needs review"

A manual category is never overwritten.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from centavo.auth.models import User
from centavo.categories.models import CategoryRule
from centavo.categorization.cache import ClassifierCache
from centavo.categorization.classifier import CategoryClassifier
from centavo.categorization.rules import Rule, RuleMatcher
from centavo.transactions.models import CategorySource, Transaction

# Below this the model is guessing; the user is asked instead.
MIN_CONFIDENCE = 0.55


@dataclass(frozen=True, slots=True)
class CategorizationResult:
    by_rule: int
    by_model: int
    left_for_review: int

    @property
    def categorized(self) -> int:
        return self.by_rule + self.by_model


class CategorizationService:
    def __init__(self, session: Session, cache: ClassifierCache) -> None:
        self._session = session
        self._cache = cache

    def categorize(self, user_id: int, transactions: Sequence[Transaction]) -> CategorizationResult:
        """Fills in the category of every transaction that was not categorized by hand."""
        pending = [item for item in transactions if item.category_source is not CategorySource.MANUAL]

        if not pending:
            return CategorizationResult(by_rule=0, by_model=0, left_for_review=0)

        without_rule: list[Transaction] = []
        matcher = RuleMatcher(self._load_rules(user_id))

        for transaction in pending:
            category_id = matcher.match(transaction.normalized_description)

            if category_id is None:
                without_rule.append(transaction)
            else:
                _assign(transaction, category_id, CategorySource.RULE, confidence=None)

        by_rule = len(pending) - len(without_rule)
        by_model = self._apply_model(user_id, without_rule)

        return CategorizationResult(
            by_rule=by_rule,
            by_model=by_model,
            left_for_review=len(without_rule) - by_model,
        )

    def recategorize_all(self, user_id: int) -> CategorizationResult:
        """Runs again over everything not categorized by hand, with what the user taught since."""
        statement = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.category_source.is_distinct_from(CategorySource.MANUAL),
        )
        transactions = self._session.scalars(statement).all()

        return self.categorize(user_id, transactions)

    def labels_changed(self, user_id: int) -> None:
        """Invalidates the cached model. Call it whenever training data changes."""
        self._session.execute(
            update(User).where(User.id == user_id).values(labels_version=User.labels_version + 1)
        )

    def _apply_model(self, user_id: int, transactions: Sequence[Transaction]) -> int:
        """Keeps the model's guess only when it is confident; clears the category otherwise."""
        if not transactions:
            return 0

        classifier = self._classifier_for(user_id)

        if classifier is None:
            for transaction in transactions:
                _assign(transaction, None, None, confidence=None)
            return 0

        predictions = classifier.predict([item.normalized_description for item in transactions])
        assigned = 0

        for transaction, prediction in zip(transactions, predictions, strict=True):
            if prediction.confidence >= MIN_CONFIDENCE:
                confidence = Decimal(str(round(prediction.confidence, 3)))
                _assign(transaction, prediction.category_id, CategorySource.MODEL, confidence)
                assigned += 1
            else:
                _assign(transaction, None, None, confidence=None)

        return assigned

    def _load_rules(self, user_id: int) -> list[Rule]:
        rows = self._session.execute(
            select(CategoryRule.category_id, CategoryRule.pattern).where(CategoryRule.user_id == user_id)
        )
        return [Rule(category_id=row.category_id, pattern=row.pattern) for row in rows]

    def _classifier_for(self, user_id: int) -> CategoryClassifier | None:
        labels_version = self._session.scalars(select(User.labels_version).where(User.id == user_id)).one()

        return self._cache.get_or_train(user_id, labels_version, lambda: self._train(user_id))

    def _train(self, user_id: int) -> CategoryClassifier | None:
        """Learns only from categories a person decided (by hand or by their rule).

        Never from the model's own guesses: training on them would turn every
        mistake into a stronger mistake.
        """
        rows = self._session.execute(
            select(Transaction.normalized_description, Transaction.category_id).where(
                Transaction.user_id == user_id,
                Transaction.category_id.is_not(None),
                Transaction.category_source.in_([CategorySource.MANUAL, CategorySource.RULE]),
            )
        ).all()

        descriptions = [row.normalized_description for row in rows]
        category_ids = [row.category_id for row in rows]

        return CategoryClassifier.train(descriptions, category_ids)


def _assign(
    transaction: Transaction,
    category_id: int | None,
    source: CategorySource | None,
    confidence: Decimal | None,
) -> None:
    transaction.category_id = category_id
    transaction.category_source = source
    transaction.category_confidence = confidence
