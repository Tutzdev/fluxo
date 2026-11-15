"""The heart of the app: rules first, then a model that learns from the user's corrections."""

STATEMENT = """date,description,amount
2026-08-02,PREZUNIC TIJUCA,-180.00
2026-08-05,GUANABARA SUPERMERCADOS,-250.00
2026-08-07,HORTIFRUTI BARRA,-45.00
2026-08-09,IFOOD *IFOOD,-60.00
2026-08-12,BOTECO DO ZE,-90.00
2026-08-15,UBER *TRIP,-25.00
2026-08-18,POSTO SHELL,-200.00
2026-09-02,PREZUNIC TIJUCA,-210.00
2026-09-05,GUANABARA SUPERMERCADOS,-230.00
2026-09-09,IFOOD *IFOOD,-52.00
2026-09-12,BOTECO DO ZE,-110.00
2026-09-15,UBER *TRIP,-31.00
2026-10-02,PREZUNIC BOTAFOGO,-160.00
2026-10-05,GUANABARA SUPERMERCADOS,-199.00
2026-10-15,UBER *TRIP,-19.00
2026-10-20,LOJA ALEATORIA XPTO,-77.00
"""


def unknown_ids(api):
    return [item["id"] for item in api.get("/api/transactions", needs_review="true").json["items"]]


def find(api, text):
    return api.get("/api/transactions", search=text).json["items"]


def test_what_no_rule_knows_waits_for_review(api):
    account_id = api.create_account()

    result = api.import_csv(account_id, STATEMENT).json

    assert result["categorized_count"] == 10
    assert {item["description"] for item in find(api, "prezunic")} == {"PREZUNIC TIJUCA", "PREZUNIC BOTAFOGO"}
    assert all(item["needs_review"] for item in find(api, "prezunic"))


def test_one_correction_teaches_the_model_the_rest(api):
    account_id = api.create_account()
    api.import_csv(account_id, STATEMENT)
    groceries = api.category_id("Groceries")
    oldest_prezunic = find(api, "prezunic")[-1]

    corrected = api.put(f"/api/transactions/{oldest_prezunic['id']}/category", {"category_id": groceries})
    result = api.post("/api/transactions/recategorize").json["recategorized"]

    assert corrected.json["category_source"] == "manual"
    assert result["by_model"] >= 2
    learned = [item for item in find(api, "prezunic") if item["id"] != oldest_prezunic["id"]]
    assert {item["category_id"] for item in learned} == {groceries}
    assert {item["category_source"] for item in learned} == {"model"}
    assert all(float(item["category_confidence"]) >= 0.55 for item in learned)


def test_something_the_model_has_never_seen_stays_in_review(api):
    account_id = api.create_account()
    api.import_csv(account_id, STATEMENT)
    first_prezunic = find(api, "prezunic tijuca")[-1]
    api.put(
        f"/api/transactions/{first_prezunic['id']}/category", {"category_id": api.category_id("Groceries")}
    )

    api.post("/api/transactions/recategorize")

    assert find(api, "aleatoria")[0]["needs_review"]


def test_a_new_rule_applies_to_past_transactions_too(api):
    account_id = api.create_account()
    api.import_csv(account_id, STATEMENT)
    restaurants = api.category_id("Restaurants")

    response = api.post(f"/api/categories/{restaurants}/rules", {"pattern": "boteco do zé"})

    assert response.status_code == 201
    assert response.json["rule"]["pattern"] == "BOTECO DO ZE"
    assert {item["category_source"] for item in find(api, "boteco")} == {"rule"}
    assert {item["category_id"] for item in find(api, "boteco")} == {restaurants}


def test_a_manual_category_is_never_overwritten(api):
    account_id = api.create_account()
    api.import_csv(account_id, STATEMENT)
    boteco = find(api, "boteco")[0]
    leisure = api.category_id("Leisure")
    api.put(f"/api/transactions/{boteco['id']}/category", {"category_id": leisure})

    api.post(f"/api/categories/{api.category_id('Restaurants')}/rules", {"pattern": "BOTECO"})
    api.post("/api/transactions/recategorize")

    after = next(item for item in find(api, "boteco") if item["id"] == boteco["id"])
    assert (after["category_id"], after["category_source"]) == (leisure, "manual")


def test_a_rule_needs_letters_and_must_be_new(api):
    groceries = api.category_id("Groceries")

    digits_only = api.post(f"/api/categories/{groceries}/rules", {"pattern": "12345"})
    duplicate = api.post(f"/api/categories/{groceries}/rules", {"pattern": "carrefour"})

    assert digits_only.status_code == 422
    assert duplicate.status_code == 409


def test_deleting_a_category_sends_its_transactions_back_to_review(api):
    account_id = api.create_account()
    api.import_csv(account_id, STATEMENT)
    transport = api.category_id("Transport")
    in_transport = api.get("/api/transactions", category_id=transport).json["total"]
    before = len(unknown_ids(api))

    api.delete(f"/api/categories/{transport}")

    assert in_transport > 0
    assert len(unknown_ids(api)) == before + in_transport
