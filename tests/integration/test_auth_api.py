from datetime import timedelta

from tests.conftest import Api, sign_up


def test_signing_up_returns_a_token_and_a_starter_set_of_categories(client):
    api = sign_up(client)

    me = api.get("/api/auth/me")
    categories = api.get("/api/categories").json["items"]

    assert me.status_code == 200
    assert me.json["email"] == "ana@example.com"
    assert {"Groceries", "Restaurants", "Salary", "Transfers"} <= {
        category["name"] for category in categories
    }
    assert any(category["rules"] for category in categories)


def test_an_email_can_only_have_one_account_whatever_its_case(client):
    sign_up(client, email="ana@example.com")

    response = client.post(
        "/api/auth/register",
        json={"name": "Ana", "email": "ANA@example.com", "password": "another long password"},
    )

    assert response.status_code == 409
    assert response.json["code"] == "EMAIL_TAKEN"


def test_a_short_password_is_rejected_with_the_field_that_failed(client):
    response = client.post(
        "/api/auth/register", json={"name": "Ana", "email": "ana@example.com", "password": "short"}
    )

    assert response.status_code == 422
    assert response.content_type == "application/problem+json"
    assert response.json["fields"][0]["field"] == "password"


def test_logging_in_with_the_right_password_gives_a_new_token(client):
    sign_up(client)

    response = client.post(
        "/api/auth/login", json={"email": "ana@example.com", "password": "correct horse battery"}
    )

    assert response.status_code == 200
    assert Api(client, response.json["token"]).get("/api/auth/me").status_code == 200


def test_a_wrong_email_and_a_wrong_password_look_the_same(client):
    sign_up(client)

    wrong_password = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "nope"})
    wrong_email = client.post("/api/auth/login", json={"email": "bia@example.com", "password": "nope"})

    assert wrong_password.status_code == wrong_email.status_code == 401
    assert wrong_password.json == wrong_email.json


def test_too_many_wrong_passwords_lock_the_email_for_a_while(client):
    sign_up(client)

    for _ in range(5):
        client.post("/api/auth/login", json={"email": "ana@example.com", "password": "nope"})

    response = client.post(
        "/api/auth/login", json={"email": "ana@example.com", "password": "correct horse battery"}
    )

    assert response.status_code == 429


def test_every_private_endpoint_needs_a_token(client):
    response = client.get("/api/accounts")

    assert response.status_code == 401
    assert response.json["code"] == "MISSING_TOKEN"


def test_logging_out_kills_the_token(api):
    assert api.post("/api/auth/logout").status_code == 204

    assert api.get("/api/auth/me").status_code == 401


def test_tokens_expire(api, clock):
    clock.advance(timedelta(days=31))

    response = api.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json["code"] == "INVALID_TOKEN"
