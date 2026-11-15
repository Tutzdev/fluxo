"""Keyword rules: the user's explicit word on what a description means."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rule:
    category_id: int
    pattern: str


class RuleMatcher:
    """Finds the rule whose pattern appears in a description as whole words.

    Whole words, so 'MERCADO' does not catch 'MERCADOPAGO'. When several rules
    match, the most specific one wins: 'AMAZON PRIME' beats 'AMAZON'.
    """

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules = sorted(rules, key=_specificity, reverse=True)

    def match(self, normalized_description: str) -> int | None:
        padded = f" {normalized_description} "

        for rule in self._rules:
            if f" {rule.pattern} " in padded:
                return rule.category_id

        return None


def _specificity(rule: Rule) -> tuple[int, int]:
    return len(rule.pattern.split()), len(rule.pattern)
