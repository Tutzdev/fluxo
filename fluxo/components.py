"""The long-lived objects of one app instance, built once in create_app()."""

from dataclasses import dataclass

from flask import current_app

from fluxo.auth.throttle import LoginThrottle
from fluxo.categorization.cache import ClassifierCache
from fluxo.clock import Clock
from fluxo.config import Settings


@dataclass(frozen=True, slots=True)
class Components:
    settings: Settings
    clock: Clock
    classifier_cache: ClassifierCache
    login_throttle: LoginThrottle


def components() -> Components:
    found: Components = current_app.extensions["fluxo"]
    return found
