"""Keeps each user's trained classifier until what it learned from changes."""

import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

from fluxo.categorization.classifier import CategoryClassifier

DEFAULT_CAPACITY = 256


@dataclass(frozen=True, slots=True)
class _Entry:
    labels_version: int
    classifier: CategoryClassifier | None


class ClassifierCache:
    """A small LRU of classifiers keyed by user, validated by the user's labels_version.

    Training takes milliseconds for a personal statement history, so nothing is
    persisted: no model files to migrate, and no pickles to trust. A process
    that restarts just trains again on first use.
    """

    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        self._capacity = capacity
        self._entries: OrderedDict[int, _Entry] = OrderedDict()
        self._lock = threading.Lock()

    def get_or_train(
        self,
        user_id: int,
        labels_version: int,
        train: Callable[[], CategoryClassifier | None],
    ) -> CategoryClassifier | None:
        with self._lock:
            entry = self._entries.get(user_id)

            if entry is not None and entry.labels_version == labels_version:
                self._entries.move_to_end(user_id)
                return entry.classifier

        classifier = train()

        with self._lock:
            self._entries[user_id] = _Entry(labels_version, classifier)
            self._entries.move_to_end(user_id)

            while len(self._entries) > self._capacity:
                self._entries.popitem(last=False)

        return classifier
