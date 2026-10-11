from flask import Flask, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from realworld.api.routes.v1.users.routes import users_blueprint
from realworld.api.routes.v1.profiles.routes import profiles_blueprint
from realworld.api.routes.v1.articles.routes import articles_blueprint, tags_blueprint


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    return app


def _register_blueprints(app: Flask):
    app.register_blueprint(articles_blueprint, url_prefix="/api")
    app.register_blueprint(users_blueprint, url_prefix="/api")
    app.register_blueprint(
        profiles_blueprint, url_prefix=f"/api{profiles_blueprint.url_prefix}"
    )
    app.register_blueprint(
        tags_blueprint, url_prefix=f"/api{tags_blueprint.url_prefix}"
    )

    @app.route("/api/ping")
    def ping():
        return "pong"


def _register_error_handlers(app: Flask):
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = jsonify({"error": "Validation error", "messages": error.errors()})
        response.status_code = 422
        return response


app = create_app()
