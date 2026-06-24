import os

from flask import Flask

from .config import Config
from .extensions import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from .routes import api

    app.register_blueprint(api)

    with app.app_context():
        if app.config["AUTO_INIT_DB"]:
            db.create_all()
            from .migrations import ensure_runtime_schema

            ensure_runtime_schema()
            if app.config["SEED_SAMPLE_DATA"]:
                from .seed import seed_defaults

                seed_defaults()

    return app
