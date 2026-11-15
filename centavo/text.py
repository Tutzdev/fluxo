"""Turns bank statement descriptions into something rules, models and humans can compare."""

import re
import unicodedata

_NON_ALPHANUMERIC = re.compile(r"[^A-Z0-9]+")
_HAS_LETTER = re.compile(r"[A-Z]")


def normalize_description(description: str) -> str:
    """'Uber *Trip 12/11 Sao Paulo' and 'UBER TRIP 13/11 SÃO PAULO' become the same text.

    Uppercase, no accents, no punctuation, and no tokens without a letter
    (dates, installment counters and card numbers change on every line).
    """
    without_accents = unicodedata.normalize("NFKD", description).encode("ascii", "ignore").decode()
    words = _NON_ALPHANUMERIC.split(without_accents.upper())

    return " ".join(word for word in words if _HAS_LETTER.search(word))
