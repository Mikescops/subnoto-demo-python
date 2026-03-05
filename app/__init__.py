"""Flask application factory."""

from flask import Flask

from app import config
from app.routes import quotes_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="",
        template_folder="templates",
    )
    app.register_blueprint(quotes_bp)
    return app
