"""The main module for plotting user related graphs."""
import os
from sqlalchemy import or_
from datetime import timedelta

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributer import Contributer

from .helper.db import get_user_repositories, get_user_commits
from .plotting.commit_timeline import plot_commit_timeline
from .plotting.commit_punchcard import plot_commit_punchcard
from .plotting.repository_changes import plot_repository_changes
from .plotting.contributer_travel_path import contributer_travel_path


def plot_user_commit_timeline(contributer, path):
    """Get all commits of repositories of an user."""
    commits = get_user_commits(contributer)
    title = f"{contributer.login}'s commit size history."
    path = os.path.join(path, 'commit_timeline')

    plot_commit_timeline(commits, path, title)


def plot_user_repositories_changes(contributer, path):
    """Box plot the contributions to a specific repository."""
    path = os.path.join(path, 'repo_changes')
    if not os.path.exists(path):
        os.makedirs(path)
    repositories = get_user_repositories(contributer)
    for repository in repositories:
        commits = db.session.query(Commit) \
            .filter(Commit.repository == repository) \
            .join(Email, or_(
                Email.email == Commit.author_email_address,
                Email.email == Commit.committer_email_address,
            )) \
            .join(Contributer, Email.contributer_login == Contributer.login) \
            .filter(Contributer.login == contributer.login) \
            .all()

        # Don't plot for too few contributions
        if len(commits) < 20:
            continue

        name = repository.full_name.replace('/', '---')
        plot_path = os.path.join(path, name)
        title = ('Commit size history for repository '
                 f'`{repository.name}` and contributer `{contributer.login}`')
        plot_repository_changes(commits, plot_path, title)


def plot_user_punchcard(contributer, path):
    """Get all commits of repositories of an user."""
    delta = timedelta(days=364)
    commits = get_user_commits(contributer, delta)

    path = os.path.join(path, 'punchcard')

    title = f"{contributer.login}'s Punchcard"

    plot_commit_punchcard(commits, path, title)


def plot_user_travel_path(contributer, path):
    """Get the user utcoffset changes."""
    commits = get_user_commits(contributer)

    title = f"{contributer.login}'s Travel history"
    contributer_travel_path(commits, path, title)

    """Plot the travel timeline of an user."""
