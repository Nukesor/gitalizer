"""The main module for plotting graphs."""
import os
import sys
from sqlalchemy import or_

from gitalizer.helper import get_config
from gitalizer.extensions import logger
from gitalizer.models.contributor import Contributor
from .user import (
    plot_user_punchcard,
    plot_user_travel_path,
)
from .employee import (
    plot_employee_timeline_with_holiday,
    plot_employee_punchcard,
    plot_employee_missing_time,
)
from .comparison import (
    plot_compare_employee_missing_time,
)


def plot_user(login, session):
    """Plot all user related graphs."""
    plot_dir = get_config().PLOT_DIR
    if not os.path.exists(plot_dir):
        os.mkdir(plot_dir)

    user_dir = os.path.join(plot_dir, login.lower())
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)

    contributor = session.query(Contributor) \
        .filter(Contributor.login.ilike(login)) \
        .one_or_none()

    if contributor is None:
        logger.info(f'No contributor with name {login}')
        sys.exit(1)

    plot_user_travel_path(contributor, user_dir, session)
    plot_user_punchcard(contributor, user_dir, session)
#    plot_user_commit_timeline(contributor, user_dir)


def plot_employee(login, repositories, session):
    """Plot all user related graphs."""
    plot_dir = get_config().PLOT_DIR
    path = os.path.join(plot_dir, login.lower(), 'employee')
    os.makedirs(path, exist_ok=True)

    contributor = session.query(Contributor) \
        .filter(Contributor.login.ilike(login)) \
        .one_or_none()

    from gitalizer.models import Repository
    conditions = []
    for name in repositories:
        conditions.append(Repository.full_name.ilike(name))

    repositories = session.query(Repository) \
        .filter(or_(*conditions)) \
        .all()

    if contributor is None:
        logger.info(f'No contributor with name {login}')
        sys.exit(1)
    elif len(repositories) == 0:
        logger.info('No repositories found with these names.')
        sys.exit(1)

    plot_employee_punchcard(contributor, repositories, path, session)
    plot_employee_timeline_with_holiday(contributor, repositories, path, session)
    plot_employee_missing_time(contributor, repositories, path, session)


def plot_comparison(logins, repositories, session):
    """Compare multiple persons for specific repositories."""
    plot_dir = get_config().PLOT_DIR
    path = os.path.join(plot_dir, 'comparison')
    os.makedirs(path, exist_ok=True)

    contributors = []
    for login in logins.split(','):
        contributor = session.query(Contributor) \
            .filter(Contributor.login.ilike(login)) \
            .one()
        contributors.append(contributor)

    from gitalizer.models import Repository
    conditions = []
    for name in repositories:
        conditions.append(Repository.full_name.ilike(name))

    repositories = session.query(Repository) \
        .filter(or_(*conditions)) \
        .all()

    plot_compare_employee_missing_time(contributors, repositories, path, session)
#    plot_compare_employee_commits(contributors, repositories, path)
