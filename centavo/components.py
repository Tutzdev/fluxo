"""The long-lived objects of one app instance, built once in create_app()."""

from dataclasses import dataclass

from flask import current_app

from centavo.auth.throttle import LoginThrottle
from centavo.categorization.cache import ClassifierCache
from centavo.clock import Clock
from centavo.config import Settings


@dataclass(frozen=True, slots=True)
class Components:
    settings: Settings
    clock: Clock
    classifier_cache: ClassifierCache
    login_throttle: LoginThrottle


def components() -> Components:
    found: Components = current_app.extensions["centavo"]
    return found
