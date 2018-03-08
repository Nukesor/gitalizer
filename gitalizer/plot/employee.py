"""The main module for plotting user related graphs."""
import os
from datetime import timedelta

from .helper.db import get_user_commits_from_repositories
from .plotting import (
    CommitTimeline,
    CommitPunchcard,
    MissingTime,
)


def plot_employee_timeline_with_holiday(contributer, repositories, path):
    """Get all commits of repositories of an user."""
    commits = get_user_commits_from_repositories(contributer, repositories)
    title = f"{contributer.login}'s commit size history."
    path = os.path.join(path, 'commit_timeline')

    plotter = CommitTimeline(commits, path, title)
    plotter.run()


def plot_employee_punchcard(contributer, repositories, path):
    """Get all commits of repositories of an user."""
    delta = timedelta(days=364)
    commits = get_user_commits_from_repositories(contributer, repositories, delta)
    path = os.path.join(path, 'punchcard')
    title = f"{contributer.login}'s Punchcard"

    plotter = CommitPunchcard(commits, path, title)
    plotter.run()


def plot_employee_missing_time(contributer, repositories, path):
    """Plot a timeline with marked missing times."""
    delta = timedelta(days=364)
    commits = get_user_commits_from_repositories(contributer, repositories, delta)
    title = f"{contributer.login}'s Missing times"

    plotter = MissingTime(commits, path, title)
    plotter.run()
