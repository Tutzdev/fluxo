"""Entry point for gunicorn and `flask --app fluxo.wsgi run`."""

from fluxo.app import create_app

app = create_app()
