"""The main module for plotting user related graphs."""
import os
from datetime import timedelta

from .helper.db import get_user_commits_from_repositories
from .plotting import (
    CommitTimeline,
    CommitPunchcard,
    MissingTime,
)


def plot_employee_timeline_with_holiday(contributor, repositories, path):
    """Get all commits of repositories of an user."""
    commits = get_user_commits_from_repositories(contributor, repositories)
    title = f"{contributor.login}'s commit size history."
    path = os.path.join(path, 'commit_timeline')

    plotter = CommitTimeline(commits, path, title)
    plotter.run()


def plot_employee_punchcard(contributor, repositories, path):
    """Get all commits of repositories of an user."""
    delta = timedelta(days=364)
    commits = get_user_commits_from_repositories(contributor, repositories, delta)
    path = os.path.join(path, 'punchcard')
    title = f"{contributor.login}'s Punchcard"

    plotter = CommitPunchcard(commits, path, title)
    plotter.run()


def plot_employee_missing_time(contributor, repositories, path):
    """Plot a timeline with marked missing times."""
    delta = timedelta(days=364)
    commits = get_user_commits_from_repositories(contributor, repositories, delta)
    title = f"{contributor.login}'s Missing times"

    plotter = MissingTime(commits, path, title)
    plotter.run()
