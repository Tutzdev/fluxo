from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"

OCTOBER = """date,description,amount
2026-10-30,CAFE DA ESQUINA,-6.50
2026-10-30,CAFE DA ESQUINA,-6.50
2026-10-31,IFOOD *IFOOD,-45.00
"""

LAST_THIRTY_DAYS = """date,description,amount
2026-10-30,CAFE DA ESQUINA,-6.50
2026-10-30,CAFE DA ESQUINA,-6.50
2026-10-31,IFOOD *IFOOD,-45.00
2026-11-03,UBER *TRIP,-23.00
"""


def test_importing_the_same_file_twice_imports_nothing_the_second_time(api):
    account_id = api.create_account()
    content = (FIXTURES / "nubank-checking.csv").read_bytes()

    first = api.import_file(account_id, content, "nubank.csv")
    second = api.import_file(account_id, content, "nubank.csv")

    assert (first.json["imported_count"], first.json["duplicate_count"]) == (3, 0)
    assert (second.json["imported_count"], second.json["duplicate_count"]) == (0, 3)
    assert api.get("/api/transactions").json["total"] == 3


def test_overlapping_exports_only_add_what_is_new_and_keep_real_twin_purchases(api):
    account_id = api.create_account()

    api.import_csv(account_id, OCTOBER)
    overlap = api.import_csv(account_id, LAST_THIRTY_DAYS)

    assert overlap.json["imported_count"] == 1
    assert overlap.json["duplicate_count"] == 3
    assert api.get("/api/transactions", search="cafe").json["total"] == 2


def test_the_same_line_in_two_accounts_is_two_transactions(api):
    checking = api.create_account("Checking")
    savings = api.create_account("Savings", kind="savings")

    api.import_csv(checking, OCTOBER)
    second = api.import_csv(savings, OCTOBER)

    assert second.json["imported_count"] == 3


def test_ofx_files_are_read_and_their_bank_ids_used(api):
    account_id = api.create_account()
    content = (FIXTURES / "itau-sgml.ofx").read_bytes()

    first = api.import_file(account_id, content, "extrato.ofx")
    second = api.import_file(account_id, content, "extrato.ofx")

    assert first.json["file_format"] == "ofx"
    assert first.json["imported_count"] == 2
    assert second.json["duplicate_count"] == 2


def test_credit_card_exports_can_be_flipped_so_purchases_are_negative(api):
    card = api.create_account("Card", kind="credit_card")
    content = (FIXTURES / "nubank-card.csv").read_bytes()

    api.import_file(card, content, "card.csv", invert_amounts=True)

    amounts = {item["description"]: item["amount"] for item in api.get("/api/transactions").json["items"]}
    assert amounts["Ifood *Ifood"] == "-58.90"
    assert amounts["Pagamento recebido"] == "1500.00"


def test_starter_rules_categorize_well_known_merchants_on_import(api):
    card = api.create_account("Card", kind="credit_card")

    result = api.import_file(
        card, (FIXTURES / "nubank-card.csv").read_bytes(), "card.csv", invert_amounts=True
    )

    assert result.json["categorized_count"] == 4
    ifood = api.get("/api/transactions", search="ifood").json["items"][0]
    assert ifood["category_id"] == api.category_id("Restaurants")
    assert ifood["category_source"] == "rule"


def test_a_file_that_is_not_a_statement_is_explained(api):
    account_id = api.create_account()

    response = api.import_csv(account_id, "name,age\nAna,30\n")

    assert response.status_code == 422
    assert response.json["code"] == "UNREADABLE_STATEMENT"
    assert "No date column" in response.json["detail"]


def test_recent_imports_are_listed_newest_first(api):
    account_id = api.create_account()
    api.import_csv(account_id, OCTOBER)
    api.import_csv(account_id, LAST_THIRTY_DAYS)

    imports = api.get("/api/imports").json["items"]

    assert [item["imported_count"] for item in imports] == [1, 3]
