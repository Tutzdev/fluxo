from tests.conftest import sign_up

STATEMENT = """date,description,amount
2026-10-28,PADARIA SÃO JOÃO,-15.00
2026-11-01,SALARIO ACME,6800.00
2026-11-03,PADARIA SÃO JOÃO,-12.00
2026-11-04,LOJA DO CHICO,-99.90
2026-11-05,UBER *TRIP,-23.45
"""


def test_filters_by_month_and_sums_income_and_expenses_across_pages(api):
    api.import_csv(api.create_account(), STATEMENT)

    page = api.get("/api/transactions", month="2026-11", page_size=2).json

    assert page["total"] == 4
    assert len(page["items"]) == 2
    assert page["income"] == "6800.00"
    assert page["expenses"] == "-135.35"


def test_newest_first(api):
    api.import_csv(api.create_account(), STATEMENT)

    items = api.get("/api/transactions").json["items"]

    assert [item["occurred_on"] for item in items] == sorted(
        (item["occurred_on"] for item in items), reverse=True
    )


def test_search_ignores_accents_and_case(api):
    api.import_csv(api.create_account(), STATEMENT)

    assert api.get("/api/transactions", search="padaria sao joao").json["total"] == 2
    assert api.get("/api/transactions", search="100%").json["total"] == 0


def test_a_transaction_typed_by_hand_is_categorized_like_an_imported_one(api):
    account_id = api.create_account()

    by_rule = api.post(
        "/api/transactions",
        {
            "account_id": account_id,
            "occurred_on": "2026-11-10",
            "description": "Uber viagem",
            "amount": "-18.00",
        },
    )
    by_hand = api.post(
        "/api/transactions",
        {
            "account_id": account_id,
            "occurred_on": "2026-11-10",
            "description": "Feira",
            "amount": "-40.00",
            "category_id": api.category_id("Groceries"),
        },
    )

    assert by_rule.status_code == 201
    assert (by_rule.json["category_id"], by_rule.json["category_source"]) == (
        api.category_id("Transport"),
        "rule",
    )
    assert by_hand.json["category_source"] == "manual"


def test_an_amount_of_zero_is_rejected(api):
    response = api.post(
        "/api/transactions",
        {"account_id": api.create_account(), "occurred_on": "2026-11-10", "description": "X", "amount": "0"},
    )

    assert response.status_code == 422


def test_a_category_from_another_user_cannot_be_used(api, client):
    api.import_csv(api.create_account(), STATEMENT)
    transaction_id = api.get("/api/transactions").json["items"][0]["id"]
    other_users_category = sign_up(client, email="bia@example.com").category_id("Groceries")

    response = api.put(f"/api/transactions/{transaction_id}/category", {"category_id": other_users_category})

    assert response.status_code == 404
    assert response.json["code"] == "CATEGORY_NOT_FOUND"


def test_clearing_the_category_sends_it_back_to_review(api):
    api.import_csv(api.create_account(), STATEMENT)
    uber = api.get("/api/transactions", search="uber").json["items"][0]

    response = api.put(f"/api/transactions/{uber['id']}/category", {"category_id": None})

    assert response.json["needs_review"] is True
    assert response.json["category_source"] is None


def test_an_invalid_month_is_a_validation_error(api):
    response = api.get("/api/transactions", month="2026-13")

    assert response.status_code == 422
    assert response.json["fields"][0]["field"] == "month"
