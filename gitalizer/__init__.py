"""This package initializes the whole app with all of its modules.

This particular file additionally contains the applications factory.
"""

import os
import sys
from gitalizer.helpers.config import config
from gitalizer.extensions import logger, db, sentry, github

# Import models to load them into the declarative base of the current db engine
from gitalizer.models import * # noqa

# Entry point for click command line interaction
from gitalizer.cli import cli # noqa


class App:
    """A class representing the app."""

    def __init__(self, db, github, logger, sentry):
        """Create a new app."""
        self.db = db
        self.github = github
        self.logger = logger
        self.sentry = sentry


def create_app():
    """Create a new app."""
    # Check if the git clone dir can be created/accessed
    git_clone_dir = config['cloning']['temporary_clone_path']
    if not os.path.exists(git_clone_dir):
        try:
            os.makedirs(git_clone_dir)
        except PermissionError:
            logger.error(f"Gitalizer needs to have permissions to create the directory specified in 'GIT_CLONE_PATH': {git_clone_dir}")
            sys.exit(1)
    else:
        if not os.access(git_clone_dir, os.W_OK):
            logger.error(f"Gitalizer needs to have permissions to write to the directory specified in 'GIT_CLONE_PATH': {git_clone_dir}")
            sys.exit(1)

    return App(db, github, logger, sentry)


app = create_app()
