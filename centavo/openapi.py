"""OpenAPI metadata shared by every blueprint."""

from typing import Any

from flask_openapi3 import Info
from flask_openapi3.models import SecurityScheme

INFO = Info(
    title="Centavo API",
    version="1.0.0",
    description="Import bank statements, let the app learn your categories, see where the month is going.",
)

SECURITY_SCHEMES: dict[str, SecurityScheme | dict[str, Any]] = {
    "bearer": {"type": "http", "scheme": "bearer"}
}

BEARER_SECURITY: list[dict[str, list[str]]] = [{"bearer": []}]
