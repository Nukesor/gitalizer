"""This package contains the whole gitalizer with all of its models, views and other modules.

This particular file additionally contains the applications factory.
"""

from flask import Flask


def create_app(config_name):
    """Flask app factory function.

    It takes a `config_name` of the specific configuration to use for this instantiation.
    """
    app = Flask(__name__, static_folder=None)

    from gitalizer.config import configs
    app.config.from_object(configs[config_name])

    # Initialize extensions
    from gitalizer.extensions import db, passlib
    db.init_app(app)
    passlib.init_app(app)

    # Initialize handlers
    from gitalizer.handlers import register_handlers
    register_handlers(app)

    # Initialize blueprints
    from gitalizer.api import api
    app.register_blueprint(api)

    # Initialize custom commands
    from gitalizer.cli import register_cli
    register_cli(app)

    return app
