"""Application factory."""

import logging

from flask_openapi3 import OpenAPI

from centavo.accounts.routes import blueprint as accounts
from centavo.auth.routes import private as auth_private
from centavo.auth.routes import public as auth_public
from centavo.auth.throttle import LoginThrottle
from centavo.categories.routes import blueprint as categories
from centavo.categorization.cache import ClassifierCache
from centavo.clock import Clock, SystemClock
from centavo.components import Components
from centavo.config import Settings
from centavo.database import Database
from centavo.errors import register_error_handlers, validation_problem
from centavo.openapi import INFO, SECURITY_SCHEMES

API_BLUEPRINTS = (auth_public, auth_private, accounts, categories)


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> OpenAPI:
    settings = settings or Settings.from_env()
    clock = clock or SystemClock(settings.timezone)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = OpenAPI(
        __name__,
        info=INFO,
        security_schemes=SECURITY_SCHEMES,
        validation_error_status=422,
        validation_error_callback=validation_problem,
        doc_prefix="/api/docs",
    )
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_bytes
    app.json.sort_keys = False  # type: ignore[attr-defined]

    app.extensions["centavo"] = Components(
        settings=settings,
        clock=clock,
        classifier_cache=ClassifierCache(),
        login_throttle=LoginThrottle(),
    )
    Database(settings.database_url).init_app(app)

    register_error_handlers(app)
    _register_blueprints(app, settings)

    @app.get("/api/health", doc_ui=False)
    def health() -> dict[str, str]:
        return {"status": "up"}

    return app


def _register_blueprints(app: OpenAPI, settings: Settings) -> None:
    for blueprint in API_BLUEPRINTS:
        app.register_api(blueprint)
