from centavo.text import normalize_description


def test_ignores_case_accents_and_punctuation():
    assert normalize_description("Padaria São João - Ltda.") == "PADARIA SAO JOAO LTDA"


def test_drops_tokens_without_letters_because_they_change_on_every_line():
    assert normalize_description("Uber *Trip 12/11 #4421") == normalize_description("UBER TRIP 13/11 #9981")


def test_keeps_tokens_that_mix_letters_and_digits():
    assert normalize_description("SPOTIFY P2B7F9") == "SPOTIFY P2B7F9"


def test_empty_when_there_are_no_words():
    assert normalize_description("123 / 456") == ""
