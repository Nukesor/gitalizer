"""This module contains various extensions which will serve as a globally initialized import location."""
from gitalizer.helpers.config import config
from .github import Github
from .sentry import Sentry
from .logger import init_logging
from .sqlalchemy import DB

db = DB(config)
github = Github(config)
sentry = Sentry(config)
logger = init_logging(config)
