"""A small text classifier trained on one user's own categorized transactions."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Self

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline

MIN_EXAMPLES = 8
MIN_CATEGORIES = 2


@dataclass(frozen=True, slots=True)
class Prediction:
    category_id: int
    confidence: float


class CategoryClassifier:
    """Character n-grams + logistic regression.

    Character n-grams (not words) because bank descriptions are abbreviated and
    inconsistent: 'PAG*JOSEDASILVA', 'IFD*BURGUER', 'DROGASIL 1234' still share
    pieces with what the user already categorized. Logistic regression gives a
    real probability, which is what decides "sure enough" versus "ask the user".
    """

    def __init__(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline

    @classmethod
    def train(cls, descriptions: Sequence[str], category_ids: Sequence[int]) -> Self | None:
        """Returns None while there is too little to learn from."""
        if len(descriptions) < MIN_EXAMPLES or len(set(category_ids)) < MIN_CATEGORIES:
            return None

        pipeline = make_pipeline(
            TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True),
            LogisticRegression(C=10.0, max_iter=1000),
        )
        pipeline.fit(list(descriptions), list(category_ids))

        return cls(pipeline)

    def predict(self, descriptions: Sequence[str]) -> list[Prediction]:
        if not descriptions:
            return []

        probabilities = self._pipeline.predict_proba(list(descriptions))
        classes = self._pipeline.classes_
        predictions = []

        for row in probabilities:
            best = row.argmax()
            predictions.append(Prediction(category_id=int(classes[best]), confidence=float(row[best])))

        return predictions
