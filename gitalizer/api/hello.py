"""This is a simple example module.

Change or delete this as you see fit.
"""
from flask import g

from gitalizer.api import api
from gitalizer.schemas.user import UserSchema
from gitalizer.responses import ok


@api.route('/whoami', methods=['GET'])
def whoami():
    """Echo back the current user."""
    user_schema = UserSchema()

    return ok(data=user_schema.dump(g.current_user))
