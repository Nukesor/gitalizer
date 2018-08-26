"""This module contains various extensions which will serve as a global import location.

These extensions are instantiated here but they won't be initialized until the
factory function is called.
"""
from flask_sqlalchemy import SQLAlchemy
from gitalizer.helpers.github import Github
from gitalizer.helpers.sentry import Sentry
from flask_migrate import Migrate


db = SQLAlchemy()
github = Github()
sentry = Sentry()
migrate = Migrate()
