"""The starter kit every new user gets: categories plus rules for common Brazilian merchants.

The rules solve the cold start: the model has nothing to learn from on day one,
but 'IFOOD' is a restaurant for almost everybody. Users can edit or delete any of it.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from centavo.categories.models import Category, CategoryKind, CategoryRule


@dataclass(frozen=True, slots=True)
class StarterCategory:
    name: str
    kind: CategoryKind
    color: str
    patterns: tuple[str, ...] = ()


STARTER_CATEGORIES: tuple[StarterCategory, ...] = (
    StarterCategory(
        "Groceries",
        CategoryKind.EXPENSE,
        "#3f8f5a",
        (
            "SUPERMERCADO",
            "SUPERMERCADOS",
            "MERCADINHO",
            "CARREFOUR",
            "ASSAI",
            "ATACADAO",
            "PAO DE ACUCAR",
            "HORTIFRUTI",
            "PADARIA",
        ),
    ),
    StarterCategory(
        "Restaurants",
        CategoryKind.EXPENSE,
        "#e0743a",
        ("IFOOD", "RAPPI", "ZE DELIVERY", "MCDONALDS", "BURGER KING", "OUTBACK", "RESTAURANTE", "LANCHONETE"),
    ),
    StarterCategory(
        "Transport",
        CategoryKind.EXPENSE,
        "#3b74b8",
        ("UBER", "CABIFY", "POSTO", "SHELL", "IPIRANGA", "SEM PARAR", "VELOE", "METRO", "ESTACIONAMENTO"),
    ),
    StarterCategory(
        "Housing", CategoryKind.EXPENSE, "#8366b8", ("ALUGUEL", "CONDOMINIO", "QUINTOANDAR", "IPTU")
    ),
    StarterCategory(
        "Bills & Utilities",
        CategoryKind.EXPENSE,
        "#4f8d9c",
        ("ENEL", "SABESP", "CEDAE", "COMGAS", "CEMIG", "COPEL", "CPFL", "CLARO", "VIVO", "TIM"),
    ),
    StarterCategory(
        "Health",
        CategoryKind.EXPENSE,
        "#cf4f5b",
        ("DROGASIL", "DROGA RAIA", "RAIA", "PAGUE MENOS", "FARMACIA", "DROGARIA", "UNIMED", "SMART FIT"),
    ),
    StarterCategory(
        "Subscriptions",
        CategoryKind.EXPENSE,
        "#b0548c",
        (
            "NETFLIX",
            "SPOTIFY",
            "AMAZON PRIME",
            "DISNEY",
            "HBO",
            "GLOBOPLAY",
            "DEEZER",
            "YOUTUBE",
            "APPLE COM BILL",
        ),
    ),
    StarterCategory(
        "Shopping",
        CategoryKind.EXPENSE,
        "#c49a1c",
        (
            "AMAZON",
            "MERCADO LIVRE",
            "MERCADOLIVRE",
            "SHOPEE",
            "MAGALU",
            "AMERICANAS",
            "SHEIN",
            "ALIEXPRESS",
            "RENNER",
        ),
    ),
    StarterCategory(
        "Leisure",
        CategoryKind.EXPENSE,
        "#2a9d8f",
        ("CINEMA", "CINEMARK", "INGRESSO", "SYMPLA", "STEAM", "PLAYSTATION", "XBOX"),
    ),
    StarterCategory(
        "Education", CategoryKind.EXPENSE, "#6b7a34", ("UDEMY", "ALURA", "COURSERA", "FACULDADE", "ESCOLA")
    ),
    StarterCategory(
        "Fees & Interest", CategoryKind.EXPENSE, "#7a7f87", ("IOF", "JUROS", "TARIFA", "ANUIDADE", "MULTA")
    ),
    StarterCategory("Other", CategoryKind.EXPENSE, "#9aa1a9"),
    StarterCategory("Salary", CategoryKind.INCOME, "#2f8f5b", ("SALARIO", "PROVENTOS", "FOLHA DE PAGAMENTO")),
    StarterCategory("Other income", CategoryKind.INCOME, "#5aa772", ("RENDIMENTO", "CASHBACK", "REEMBOLSO")),
    StarterCategory(
        "Transfers",
        CategoryKind.TRANSFER,
        "#6b7280",
        ("PAGAMENTO DE FATURA", "PAGAMENTO FATURA", "PAGAMENTO RECEBIDO", "APLICACAO", "RESGATE"),
    ),
)


def create_starter_kit(session: Session, user_id: int) -> None:
    for starter in STARTER_CATEGORIES:
        category = Category(user_id=user_id, name=starter.name, kind=starter.kind, color=starter.color)
        session.add(category)
        session.flush()

        for pattern in starter.patterns:
            session.add(CategoryRule(user_id=user_id, category_id=category.id, pattern=pattern))
