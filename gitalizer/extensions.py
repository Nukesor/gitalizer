"""This module contains various extensions which will serve as a global import location.

These extensions are instantiated here but they won't be initialized until the
factory function is called.
"""
from gitalizer.helpers import get_config
from gitalizer.helpers.postgresql import DB
from gitalizer.helpers.github import Github
from gitalizer.helpers.sentry import Sentry
from gitalizer.helpers.logger import init_logging

config = get_config()

db = DB(config)
github = Github(config)
sentry = Sentry(config)
logger = init_logging(config)
