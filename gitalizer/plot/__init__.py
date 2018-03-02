"""The main module for plotting graphs."""
import os
import sys
from sqlalchemy import or_
from flask import current_app

from gitalizer.extensions import db
from gitalizer.models.contributer import Contributer
from .user import (
    plot_user_punchcard,
    plot_user_repositories_changes,
    plot_user_commit_timeline,
    plot_user_travel_path,
)
from .employee import (
    plot_employee_timeline_with_holiday,
    plot_employee_punchcard,
    plot_employee_missing_time,
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
#    plot_user_repositories_changes(contributer, user_dir)
    plot_user_commit_timeline(contributer, user_dir)
#    plot_user_travel_path(contributer, user_dir)


def plot_employee(login, repositories):
    """Plot all user related graphs."""
    plot_dir = current_app.config['PLOT_DIR']
    path = os.path.join(plot_dir, login.lower(), 'employee')
    os.makedirs(path, exist_ok=True)

    contributer = db.session.query(Contributer) \
        .filter(Contributer.login.ilike(login)) \
        .one_or_none()

    from gitalizer.models import Repository
    conditions = []
    for name in repositories:
        conditions.append(Repository.full_name.ilike(name))

    repositories = db.session.query(Repository) \
        .filter(or_(*conditions)) \
        .all()

    if contributer is None:
        print(f'No contributer with name {login}')
        sys.exit(1)
    elif len(repositories) == 0:
        print(f'No repositories found with these names.')
        sys.exit(1)

#    plot_employee_punchcard(contributer, repositories, path)
#    plot_employee_timeline_with_holiday(contributer, repositories, path)
    plot_employee_missing_time(contributer, repositories, path)
