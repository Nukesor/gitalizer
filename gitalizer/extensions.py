"""This module contains various extensions which will serve as a global import location.

These extensions are instantiated here but they won't be initialized until the
factory function is called.
"""
from flask_sqlalchemy import SQLAlchemy
from gitalizer.helpers.passlib import Passlib
from gitalizer.helpers.github import Github


db = SQLAlchemy()
passlib = Passlib()
github = Github()
