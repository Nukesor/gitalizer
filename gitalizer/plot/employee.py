"""The main module for plotting user related graphs."""
import os
from datetime import timedelta

from gitalizer.helpers.db import get_user_commits_from_repositories
from .plotting import (
    CommitTimeline,
    CommitPunchcard,
    MissingTime,
)


def plot_employee_timeline_with_holiday(contributor, repositories, path, session):
    """Get all commits of repositories of an user."""
    commits = get_user_commits_from_repositories(contributor, repositories, session)
    title = f"{contributor.login}'s commit size history."
    path = os.path.join(path, 'commit_timeline')

    plotter = CommitTimeline(commits, path, title)
    plotter.run()


def plot_employee_punchcard(contributor, repositories, path, session):
    """Get all commits of repositories of an user."""
    delta = timedelta(days=364)
    commits = get_user_commits_from_repositories(contributor, repositories, session, delta)
    path = os.path.join(path, 'punchcard')
    title = f"{contributor.login}'s Punchcard"

    plotter = CommitPunchcard(commits, path, title)
    plotter.run()


def plot_employee_missing_time(contributor, repositories, path, session):
    """Plot a timeline with marked miss-out."""
    delta = timedelta(days=364)
    commits = get_user_commits_from_repositories(contributor, repositories, session, delta)
    title = f"{contributor.login}'s miss-out"

    plotter = MissingTime(commits, path, title, delta=delta)
    plotter.run()
