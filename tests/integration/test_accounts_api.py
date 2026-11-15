from tests.conftest import sign_up

STATEMENT = "date,description,amount\n2026-11-01,SALARIO ACME,5000.00\n2026-11-02,PADARIA,-12.50\n"


def test_the_balance_is_the_opening_balance_plus_every_transaction(api):
    account_id = api.create_account("Checking", opening_balance="100.00")
    api.import_csv(account_id, STATEMENT)

    accounts = api.get("/api/accounts").json

    assert accounts["items"][0]["balance"] == "5087.50"
    assert accounts["items"][0]["transaction_count"] == 2
    assert accounts["total_balance"] == "5087.50"


def test_account_names_are_unique_per_user_ignoring_case(api, client):
    api.create_account("Nubank")

    duplicate = api.post("/api/accounts", {"name": "NUBANK", "kind": "checking"})
    someone_else = sign_up(client, email="bia@example.com").post(
        "/api/accounts", {"name": "Nubank", "kind": "cash"}
    )

    assert duplicate.status_code == 409
    assert someone_else.status_code == 201


def test_someone_elses_account_does_not_exist_for_you(api, client):
    account_id = api.create_account()
    intruder = sign_up(client, email="eve@example.com")

    assert intruder.patch(f"/api/accounts/{account_id}", {"name": "Mine now"}).status_code == 404
    assert intruder.delete(f"/api/accounts/{account_id}").status_code == 404
    assert intruder.import_csv(account_id, STATEMENT).status_code == 404


def test_deleting_an_account_takes_its_transactions_with_it(api):
    account_id = api.create_account()
    api.import_csv(account_id, STATEMENT)

    assert api.delete(f"/api/accounts/{account_id}").status_code == 204

    assert api.get("/api/transactions").json["total"] == 0
