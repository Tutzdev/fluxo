"""Money is Decimal with two places, never float."""

import re
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

CENTS = Decimal("0.01")

_CURRENCY_NOISE = re.compile(r"[R$\s ]")


def to_money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_EVEN)


def parse_amount(raw: str) -> Decimal:
    """Reads amounts written the Brazilian way or the international way.

    '1.234,56', 'R$ -45,90', '-45.90' and '1,234.56' are all understood:
    whichever separator comes last is the decimal one.
    """
    text = _CURRENCY_NOISE.sub("", raw)

    if not text:
        raise ValueError(f"Empty amount: {raw!r}")

    last_comma = text.rfind(",")
    last_dot = text.rfind(".")

    if last_comma > last_dot:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")

    try:
        return to_money(text)
    except InvalidOperation as error:
        raise ValueError(f"Not an amount: {raw!r}") from error
