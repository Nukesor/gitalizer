"""The main module for plotting user related graphs."""
import os
from sqlalchemy import or_
from datetime import timedelta

from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributor import Contributor
from gitalizer.helpers.db import get_user_repositories, get_user_commits

from .plotting import (
    CommitTimeline,
    CommitPunchcard,
    plot_repository_changes,
    TravelPath,
)


def plot_user_commit_timeline(contributor, path, session):
    """Get all commits of repositories of an user."""
    commits = get_user_commits(contributor, session)
    title = f"{contributor.login}'s commit size history."
    path = os.path.join(path, 'commit_timeline')

    plotter = CommitTimeline(commits, path, title)
    plotter.run()


def plot_user_repositories_changes(contributor, path, session):
    """Box plot the contributions to a specific repository."""
    path = os.path.join(path, 'repo_changes')
    if not os.path.exists(path):
        os.makedirs(path)
    repositories = get_user_repositories(contributor, session)
    for repository in repositories:
        commits = session.query(Commit) \
            .filter(Commit.repository == repository) \
            .join(Email, or_(
                Email.email == Commit.author_email_address,
                Email.email == Commit.committer_email_address,
            )) \
            .join(Contributor, Email.contributor_login == Contributor.login) \
            .filter(Contributor.login == contributor.login) \
            .all()

        # Don't plot for too few contributions
        if len(commits) < 20:
            continue

        name = repository.full_name.replace('/', '---')
        plot_path = os.path.join(path, name)
        title = ('Commit size history for repository '
                 f'`{repository.name}` and contributor `{contributor.login}`')
        plot_repository_changes(commits, plot_path, title)


def plot_user_punchcard(contributor, path, session):
    """Get all commits of repositories of an user."""
    delta = timedelta(days=364)
    commits = get_user_commits(contributor, session, delta)

    path = os.path.join(path, 'punchcard')

    title = f"{contributor.login}'s Punchcard"

    plotter = CommitPunchcard(commits, path, title)
    plotter.run()


def plot_user_travel_path(contributor, path, session):
    """Visualize the user utcoffset changes."""
    delta = timedelta(days=2*364)
    commits = get_user_commits(contributor, session, delta)
    path = os.path.join(path, 'travel_path')

    plotter = TravelPath(commits, path, session)
    plotter.run()
