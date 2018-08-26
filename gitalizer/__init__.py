"""This package initializes the whole app with all of its modules.

This particular file additionally contains the applications factory.
"""

import os
import sys
import matplotlib
from gitalizer.helper import get_config
from gitalizer.extensions import logger, db, sentry, github
matplotlib.use("Agg")


def create_app():
    """Create a new app."""
    config = get_config()
    # Check if the git clone dir can be created/accessed
    git_clone_dir = config.GIT_CLONE_PATH
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

    # Import models to load them into the declarative base of the current db engine
    from gitalizer.models import *

    return App(db, github, logger, sentry)


class App:
    """A class representing the app."""

    def __init__(self, db, github, logger, sentry):
        """Create a new app."""
        self.db = db
        self.github = github
        self.logger = logger
        self.sentry = sentry
