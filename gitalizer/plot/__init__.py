"""The main module for plotting graphs."""
import os
import sys
from flask import current_app

from gitalizer.extensions import db
from gitalizer.models.contributer import Contributer
from .user import (
    plot_user_punchcard,
    plot_user_repositories_changes,
    plot_user_commit_timeline,
)


def plot_user(login):
    """Plot all user related graphs."""
    plot_dir = current_app.config['PLOT_DIR']
    if not os.path.exists(plot_dir):
        os.mkdir(plot_dir)

    user_dir = os.path.join(plot_dir, login.lower())
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)

    contributer = db.session.query(Contributer) \
        .filter(Contributer.login.ilike(login)) \
        .one_or_none()

    if contributer is None:
        print(f'No contributer with name {login}')
        sys.exit(1)

    plot_user_punchcard(contributer, user_dir)
    plot_user_repositories_changes(contributer, user_dir)
    plot_user_commit_timeline(contributer, user_dir)
