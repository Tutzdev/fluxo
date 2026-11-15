CHECKING = """date,description,amount
2026-11-05,SALARIO ACME,6800.00
2026-11-10,ALUGUEL APTO,-1850.00
2026-11-12,PAGAMENTO DE FATURA,-900.00
2026-11-13,LOJA DO CHICO,-60.00
"""

CARD = """date,description,amount
2026-11-02,IFOOD *IFOOD,-120.00
2026-11-03,UBER *TRIP,-30.00
2026-11-12,PAGAMENTO RECEBIDO,900.00
"""


def with_statements(api):
    api.import_csv(api.create_account("Checking"), CHECKING)
    api.import_csv(api.create_account("Card", kind="credit_card"), CARD)


def test_paying_the_card_bill_is_not_counted_as_income_or_spending(api):
    with_statements(api)

    summary = api.get("/api/reports/summary", month="2026-11").json

    assert summary["income"] == "6800.00"
    assert summary["expenses"] == "2060.00"
    assert summary["net"] == "4740.00"
    assert "Transfers" not in [item["name"] for item in summary["by_category"]]


def test_spending_is_broken_down_by_category_biggest_first(api):
    with_statements(api)

    by_category = api.get("/api/reports/summary", month="2026-11").json["by_category"]

    assert [(item["name"], item["amount"]) for item in by_category] == [
        ("Housing", "1850.00"),
        ("Restaurants", "120.00"),
        ("Needs review", "60.00"),
        ("Transport", "30.00"),
    ]


def test_the_summary_counts_what_still_needs_review(api):
    with_statements(api)

    assert api.get("/api/reports/summary", month="2026-11").json["needs_review"] == 1


def test_the_trend_has_every_month_even_the_empty_ones(api):
    with_statements(api)

    items = api.get("/api/reports/trend", month="2026-11", months=3).json["items"]

    assert [item["month"] for item in items] == ["2026-09", "2026-10", "2026-11"]
    assert items[0] == {"month": "2026-09", "income": "0.00", "expenses": "0.00", "net": "0.00"}
    assert items[2]["net"] == "4740.00"


def test_the_summary_defaults_to_the_current_month(api):
    with_statements(api)

    assert api.get("/api/reports/summary").json["month"] == "2026-11"


def test_the_forecast_counts_bills_still_to_come(api):
    rent = "\n".join(f"2026-{month:02d}-20,CONDOMINIO EDIFICIO SOL,-650.00" for month in (8, 9, 10))
    api.import_csv(
        api.create_account("Checking", opening_balance="1000.00"), f"date,description,amount\n{rent}\n"
    )

    forecast = api.get("/api/reports/forecast").json

    assert forecast["today"] == "2026-11-15"
    assert forecast["days_left"] == 15
    assert forecast["balance_now"] == "-950.00"
    assert forecast["expected_bills"] == "-650.00"
    assert [item["expected_day"] for item in forecast["upcoming"]] == [20]
