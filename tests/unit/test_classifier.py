from fluxo.categorization.classifier import CategoryClassifier
from fluxo.categorization.service import MIN_CONFIDENCE
from fluxo.text import normalize_description

GROCERIES, RESTAURANTS, TRANSPORT = 1, 2, 3

HISTORY = [
    ("PREZUNIC TIJUCA", GROCERIES),
    ("GUANABARA SUPERMERCADOS", GROCERIES),
    ("HORTIFRUTI BARRA", GROCERIES),
    ("BOTECO DO ZE", RESTAURANTS),
    ("PIZZARIA BELLA NAPOLI", RESTAURANTS),
    ("IFD*BURGUER DO JOAO", RESTAURANTS),
    ("UBER *TRIP", TRANSPORT),
    ("POSTO SHELL BARRA", TRANSPORT),
    ("99 TECNOLOGIA", TRANSPORT),
]


def trained():
    descriptions = [normalize_description(text) for text, _ in HISTORY]
    classifier = CategoryClassifier.train(descriptions, [category for _, category in HISTORY])

    assert classifier is not None
    return classifier


def predict(classifier, *texts):
    return classifier.predict([normalize_description(text) for text in texts])


def test_does_not_train_on_too_little_data():
    assert CategoryClassifier.train(["UBER"] * 3, [TRANSPORT] * 3) is None


def test_does_not_train_on_a_single_category():
    assert CategoryClassifier.train(["UBER TRIP"] * 20, [TRANSPORT] * 20) is None


def test_recognizes_variations_of_what_it_learned():
    predictions = predict(trained(), "PREZUNIC BOTAFOGO", "UBER TRIP HELP")

    assert [prediction.category_id for prediction in predictions] == [GROCERIES, TRANSPORT]
    assert all(prediction.confidence >= MIN_CONFIDENCE for prediction in predictions)


def test_is_unsure_about_something_it_never_saw():
    [prediction] = predict(trained(), "LOJA ALEATORIA XPTO")

    assert prediction.confidence < MIN_CONFIDENCE
