"""Domain errors and their HTTP shape: Problem Details (RFC 9457) with a stable code."""

import logging
from typing import Any

from flask import Flask, Response, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"


class DomainError(Exception):
    """A rule of the domain said no. Carries the status and a code the client can switch on."""

    status = 400

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class NotFoundError(DomainError):
    status = 404


class ConflictError(DomainError):
    status = 409


class UnauthorizedError(DomainError):
    status = 401


class InvalidInputError(DomainError):
    status = 422


class TooManyRequestsError(DomainError):
    status = 429


def problem(status: int, code: str, detail: str, **extra: Any) -> Response:
    body = {"status": status, "code": code, "detail": detail, **extra}

    response = jsonify(body)
    response.status_code = status
    response.content_type = PROBLEM_JSON
    return response


def validation_problem(error: ValidationError) -> Response:
    """Called by flask-openapi3 when a request does not match its schema."""
    fields = [
        {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
        for item in error.errors(include_url=False)
    ]
    return problem(422, "INVALID_INPUT", "The request has invalid fields.", fields=fields)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(error: DomainError) -> Response:
        return problem(error.status, error.code, error.detail)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> Response:
        status = error.code or 500
        code = (error.name or "Error").upper().replace(" ", "_")
        return problem(status, code, error.description or "")

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> Response:
        log.exception("Unhandled error", exc_info=error)
        return problem(500, "INTERNAL_ERROR", "Something went wrong on our side.")
