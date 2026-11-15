from centavo.categorization.cache import ClassifierCache


class CountingTrainer:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1


def test_trains_once_per_labels_version():
    cache, train = ClassifierCache(), CountingTrainer()

    cache.get_or_train(user_id=1, labels_version=0, train=train)
    cache.get_or_train(user_id=1, labels_version=0, train=train)

    assert train.calls == 1


def test_trains_again_when_the_user_taught_something_new():
    cache, train = ClassifierCache(), CountingTrainer()

    cache.get_or_train(user_id=1, labels_version=0, train=train)
    cache.get_or_train(user_id=1, labels_version=1, train=train)

    assert train.calls == 2


def test_forgets_the_least_recently_used_user_when_full():
    cache, train = ClassifierCache(capacity=2), CountingTrainer()

    cache.get_or_train(user_id=1, labels_version=0, train=train)
    cache.get_or_train(user_id=2, labels_version=0, train=train)
    cache.get_or_train(user_id=1, labels_version=0, train=train)  # 1 is now the most recent
    cache.get_or_train(user_id=3, labels_version=0, train=train)  # evicts 2
    cache.get_or_train(user_id=2, labels_version=0, train=train)  # trains 2 again

    assert train.calls == 4
