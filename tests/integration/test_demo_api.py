from tests.conftest import Api


def start_demo(client):
    response = client.post("/api/demo/session")
    assert response.status_code == 201
    return Api(client, response.json["token"])


def test_a_demo_account_comes_with_six_months_mostly_categorized(client):
    demo = start_demo(client)

    accounts = demo.get("/api/accounts").json["items"]
    trend = demo.get("/api/reports/trend", months=6).json["items"]
    review = demo.get("/api/transactions", needs_review="true").json

    assert {account["name"] for account in accounts} == {"Nubank checking", "Nubank card"}
    assert all(month["income"] == "6800.00" for month in trend)
    assert review["total"] == 3


def test_the_demo_shows_the_model_at_work(client):
    demo = start_demo(client)

    boteco = demo.get("/api/transactions", search="boteco do ze").json["items"]

    assert {item["category_source"] for item in boteco} == {"manual", "model"}


def test_every_visitor_gets_a_separate_account(client):
    first, second = start_demo(client), start_demo(client)

    assert first.get("/api/auth/me").json["id"] != second.get("/api/auth/me").json["id"]
