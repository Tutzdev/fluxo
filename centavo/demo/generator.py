"""Six months of believable statements for the demo account.

Deterministic for a given seed, so the demo and its tests always look the same.
Some merchants match a starter rule (IFOOD, UBER), some do not (GUANABARA,
BOTECO DO ZE): those are the ones the demo "teaches" so the model can take over.
"""

import random
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from centavo.imports.parsers.base import StatementLine
from centavo.money import to_money
from centavo.month import Month


@dataclass(frozen=True, slots=True)
class Habit:
    description: str
    times_per_month: int
    min_amount: int
    max_amount: int


@dataclass(frozen=True, slots=True)
class Bill:
    description: str
    day: int
    amount: Decimal
    variation: Decimal = Decimal("0")


CHECKING_BILLS = (
    Bill("SALARIO ACME TECNOLOGIA LTDA", day=5, amount=Decimal("6800.00")),
    Bill("ALUGUEL APTO 302", day=10, amount=Decimal("-1850.00")),
    Bill("ENEL DISTRIBUICAO RIO", day=15, amount=Decimal("-182.40"), variation=Decimal("0.12")),
    Bill("CLARO FIBRA 500MB", day=20, amount=Decimal("-109.90")),
    Bill("SMART FIT MENSALIDADE", day=7, amount=Decimal("-129.90")),
)

CARD_BILLS = (
    Bill("NETFLIX.COM", day=8, amount=Decimal("-55.90")),
    Bill("SPOTIFY P2B7F9", day=14, amount=Decimal("-21.90")),
    Bill("ALURA CURSOS ONLINE", day=3, amount=Decimal("-89.90")),
)

CARD_HABITS = (
    Habit("GUANABARA SUPERMERCADOS", times_per_month=3, min_amount=90, max_amount=380),
    Habit("PREZUNIC TIJUCA", times_per_month=2, min_amount=60, max_amount=260),
    Habit("HORTIFRUTI TIJUCA", times_per_month=2, min_amount=30, max_amount=95),
    Habit("IFOOD *IFOOD", times_per_month=5, min_amount=35, max_amount=110),
    Habit("BOTECO DO ZE", times_per_month=2, min_amount=60, max_amount=180),
    Habit("PIZZARIA BELLA NAPOLI", times_per_month=1, min_amount=70, max_amount=140),
    Habit("UBER *TRIP", times_per_month=8, min_amount=11, max_amount=48),
    Habit("POSTO SHELL BARRA", times_per_month=1, min_amount=150, max_amount=260),
    Habit("DROGASIL 1123", times_per_month=1, min_amount=25, max_amount=140),
    Habit("AMAZON MARKETPLACE", times_per_month=1, min_amount=40, max_amount=320),
    Habit("CINEMARK BOTAFOGO", times_per_month=1, min_amount=40, max_amount=90),
)

# One each, in the last months: nothing matches them, so they wait in "needs review".
ONE_OFFS = ("PAG*JOAOPAULOSOUZA", "LOJA DO CHICO LTDA", "MP*VENDEDORXYZ")

CARD_BILL_PAYMENT_DAY = 12


@dataclass(frozen=True, slots=True)
class DemoStatements:
    checking: list[StatementLine]
    card: list[StatementLine]


def generate(today: date, months: int, seed: int = 7) -> DemoStatements:
    rng = random.Random(seed)
    first_month = Month.of(today).shift(-(months - 1))

    checking: list[StatementLine] = []
    card: list[StatementLine] = []
    card_total_last_month = Decimal("0")

    for offset in range(months):
        month = first_month.shift(offset)

        if card_total_last_month:
            checking.append(
                _line(month, CARD_BILL_PAYMENT_DAY, "PAGAMENTO DE FATURA NUBANK", -card_total_last_month)
            )
            card.append(_line(month, CARD_BILL_PAYMENT_DAY, "PAGAMENTO RECEBIDO", card_total_last_month))

        checking.extend(_line(month, bill.day, bill.description, _vary(bill, rng)) for bill in CHECKING_BILLS)

        card_this_month = [_line(month, bill.day, bill.description, _vary(bill, rng)) for bill in CARD_BILLS]
        card_this_month.extend(_habit_lines(month, rng))

        one_off_index = offset - (months - len(ONE_OFFS))

        if one_off_index >= 0:
            card_this_month.append(_one_off(month, today, ONE_OFFS[one_off_index], rng))

        card.extend(card_this_month)
        card_total_last_month = -sum((line.amount for line in card_this_month), start=Decimal("0"))

    return DemoStatements(checking=_until(today, checking), card=_until(today, card))


def to_csv(lines: list[StatementLine]) -> bytes:
    rows = ["date,description,amount"]
    rows.extend(f"{line.occurred_on.isoformat()},{line.description},{line.amount}" for line in lines)

    return "\n".join(rows).encode()


def _habit_lines(month: Month, rng: random.Random) -> list[StatementLine]:
    lines = []

    for habit in CARD_HABITS:
        for _ in range(habit.times_per_month):
            day = rng.randint(1, month.days)
            lines.append(
                _line(month, day, habit.description, _amount(rng, habit.min_amount, habit.max_amount))
            )

    return lines


def _one_off(month: Month, today: date, description: str, rng: random.Random) -> StatementLine:
    """On a day that already happened, so this month's one-off is not cut off as a future line."""
    last_possible_day = today.day if month == Month.of(today) else 28
    day = rng.randint(1, min(last_possible_day, 28))

    return _line(month, day, description, _amount(rng, 20, 150))


def _line(month: Month, day: int, description: str, amount: Decimal) -> StatementLine:
    return StatementLine(
        occurred_on=date(month.year, month.month, day), description=description, amount=amount
    )


def _vary(bill: Bill, rng: random.Random) -> Decimal:
    factor = Decimal(1) + Decimal(str(rng.uniform(-1, 1))) * bill.variation
    return to_money(bill.amount * factor)


def _amount(rng: random.Random, low: int, high: int) -> Decimal:
    return -to_money(Decimal(rng.randint(low * 100, high * 100)) / 100)


def _until(today: date, lines: list[StatementLine]) -> list[StatementLine]:
    return sorted((line for line in lines if line.occurred_on <= today), key=lambda line: line.occurred_on)
