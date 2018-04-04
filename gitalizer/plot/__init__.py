"""The main module for plotting graphs."""
import os
import sys
from sqlalchemy import or_
from flask import current_app

from gitalizer.extensions import db
from gitalizer.models.contributor import Contributor
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
from .comparison import (
    plot_compare_employee_missing_time,
    plot_compare_employee_commits,
)


def plot_user(login):
    """Plot all user related graphs."""
    plot_dir = current_app.config['PLOT_DIR']
    if not os.path.exists(plot_dir):
        os.mkdir(plot_dir)

    user_dir = os.path.join(plot_dir, login.lower())
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)

    contributor = db.session.query(Contributor) \
        .filter(Contributor.login.ilike(login)) \
        .one_or_none()

    if contributor is None:
        current_app.logger.info(f'No contributor with name {login}')
        sys.exit(1)

    plot_user_travel_path(contributor, user_dir)
    plot_user_punchcard(contributor, user_dir)
    plot_user_commit_timeline(contributor, user_dir)


def plot_employee(login, repositories):
    """Plot all user related graphs."""
    plot_dir = current_app.config['PLOT_DIR']
    path = os.path.join(plot_dir, login.lower(), 'employee')
    os.makedirs(path, exist_ok=True)

    contributor = db.session.query(Contributor) \
        .filter(Contributor.login.ilike(login)) \
        .one_or_none()

    from gitalizer.models import Repository
    conditions = []
    for name in repositories:
        conditions.append(Repository.full_name.ilike(name))

    repositories = db.session.query(Repository) \
        .filter(or_(*conditions)) \
        .all()

    if contributor is None:
        current_app.logger.info(f'No contributor with name {login}')
        sys.exit(1)
    elif len(repositories) == 0:
        current_app.logger.info('No repositories found with these names.')
        sys.exit(1)

    plot_employee_punchcard(contributor, repositories, path)
    plot_employee_timeline_with_holiday(contributor, repositories, path)
    plot_employee_missing_time(contributor, repositories, path)


def plot_comparison(logins, repositories):
    """Compare multiple persons for specific repositories."""
    plot_dir = current_app.config['PLOT_DIR']
    path = os.path.join(plot_dir, 'comparison')
    os.makedirs(path, exist_ok=True)

    contributors = []
    for login in logins.split(','):
        contributor = db.session.query(Contributor) \
            .filter(Contributor.login.ilike(login)) \
            .one()
        contributors.append(contributor)

    from gitalizer.models import Repository
    conditions = []
    for name in repositories:
        conditions.append(Repository.full_name.ilike(name))

    repositories = db.session.query(Repository) \
        .filter(or_(*conditions)) \
        .all()

    plot_compare_employee_missing_time(contributors, repositories, path)
    plot_compare_employee_commits(contributors, repositories, path)
