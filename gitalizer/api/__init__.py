"""lol."""
from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='')

from gitalizer.api import auth  # noqa E402
from gitalizer.api import hello  # noqa E402
