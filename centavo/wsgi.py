"""Entry point for gunicorn and `flask --app centavo.wsgi run`."""

from centavo.app import create_app

app = create_app()
