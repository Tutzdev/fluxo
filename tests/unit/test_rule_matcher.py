from centavo.categorization.rules import Rule, RuleMatcher

GROCERIES, SHOPPING, SUBSCRIPTIONS = 1, 2, 3


def test_matches_whole_words_only():
    matcher = RuleMatcher([Rule(GROCERIES, "MERCADO")])

    assert matcher.match("MERCADO DO ZE") == GROCERIES
    assert matcher.match("MERCADOPAGO VENDEDOR") is None


def test_the_most_specific_rule_wins():
    matcher = RuleMatcher([Rule(SHOPPING, "AMAZON"), Rule(SUBSCRIPTIONS, "AMAZON PRIME")])

    assert matcher.match("AMAZON PRIME BR") == SUBSCRIPTIONS
    assert matcher.match("AMAZON MARKETPLACE") == SHOPPING


def test_no_rule_no_category():
    assert RuleMatcher([]).match("ANYTHING") is None
