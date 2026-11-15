NOVEMBER = """date,description,amount
2026-10-30,IFOOD *IFOOD,-500.00
2026-11-02,IFOOD *IFOOD,-300.00
2026-11-06,RESTAURANTE SABOR,-150.00
2026-11-09,IFOOD *IFOOD,-80.00
2026-11-10,REEMBOLSO IFOOD,40.00
"""


def restaurants_budget(api, **params):
    items = api.get("/api/budgets", **params).json["items"]
    return next(item for item in items if item["category_name"] == "Restaurants")


def test_shows_what_was_spent_this_month_against_the_limit(api):
    api.import_csv(api.create_account(), NOVEMBER)
    restaurants = api.category_id("Restaurants")

    assert api.put(f"/api/budgets/{restaurants}", {"monthly_limit": "600.00"}).status_code == 204

    budget = restaurants_budget(api)
    assert budget["spent"] == "530.00"
    assert budget["remaining"] == "70.00"
    assert budget["percent_used"] == 88
    assert budget["status"] == "warning"


def test_another_month_can_be_asked_for(api):
    api.import_csv(api.create_account(), NOVEMBER)
    api.put(f"/api/budgets/{api.category_id('Restaurants')}", {"monthly_limit": "400.00"})

    october = restaurants_budget(api, month="2026-10")

    assert october["spent"] == "500.00"
    assert october["status"] == "exceeded"


def test_setting_a_limit_again_replaces_it(api):
    restaurants = api.category_id("Restaurants")

    api.put(f"/api/budgets/{restaurants}", {"monthly_limit": "600.00"})
    api.put(f"/api/budgets/{restaurants}", {"monthly_limit": "900.00"})

    budgets = api.get("/api/budgets").json["items"]
    assert [budget["monthly_limit"] for budget in budgets] == ["900.00"]


def test_only_expense_categories_can_have_a_budget(api):
    response = api.put(f"/api/budgets/{api.category_id('Salary')}", {"monthly_limit": "100.00"})

    assert response.status_code == 422
    assert response.json["code"] == "NOT_AN_EXPENSE_CATEGORY"


def test_a_limit_must_be_positive(api):
    response = api.put(f"/api/budgets/{api.category_id('Restaurants')}", {"monthly_limit": "0"})

    assert response.status_code == 422


def test_removing_a_budget_that_does_not_exist_is_a_404(api):
    restaurants = api.category_id("Restaurants")
    api.put(f"/api/budgets/{restaurants}", {"monthly_limit": "600.00"})

    assert api.delete(f"/api/budgets/{restaurants}").status_code == 204
    assert api.delete(f"/api/budgets/{restaurants}").status_code == 404
