"""This package contains the whole gitalizer with all of its models, views and other modules.

This particular file additionally contains the applications factory.
"""

import os
import sys
from flask import Flask
from gitalizer.helpers.logger import init_logging


def create_app(config_name='develop'):
    """Flask app factory function.

    It takes a `config_name` of the specific configuration to use for this instantiation.
    """
    app = Flask(__name__, static_folder=None)

    from gitalizer.config import configs
    app.config.from_object(configs[config_name])
    init_logging(app)

    # Initialize extensions
    from gitalizer.extensions import db, passlib, github, sentry, migrate
    db.init_app(app)
    passlib.init_app(app)
    github.init_app(app)
    sentry.init_app(app)
    migrate.init_app(app, db)

    # Check if the git clone dir can be created/accessed
    git_clone_dir = app.config['GIT_CLONE_PATH']
    if not os.path.exists(git_clone_dir):
        try:
            os.makedirs(git_clone_dir)
        except PermissionError:
            print(f"Gitalizer needs to have permissions to create the directory specified in 'GIT_CLONE_PATH': {git_clone_dir}")
            sys.exit(1)
    else:
        if not os.access(git_clone_dir, os.W_OK):
            print(f"Gitalizer needs to have permissions to write to the directory specified in 'GIT_CLONE_PATH': {git_clone_dir}")
            sys.exit(1)

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
