"""The main module for plotting user related graphs."""
import os
from datetime import timedelta

from .helper.db import get_user_commits_from_repositories
from .plotting.commit_timeline import plot_commit_timeline
from .plotting.commit_punchcard import plot_commit_punchcard


def plot_employee_timeline_with_holiday(contributer, repositories, path):
    """Get all commits of repositories of an user."""
    commits = get_user_commits_from_repositories(contributer, repositories)

    title = f"{contributer.login}'s commit size history."
    path = os.path.join(path, 'commit_timeline')

    plot_commit_timeline(commits, path, title)


def plot_employee_punchcard(contributer, repositories, path):
    """Get all commits of repositories of an user."""
    delta = timedelta(days=364)
    commits = get_user_commits_from_repositories(contributer, repositories, delta)

    path = os.path.join(path, 'punchcard')

    title = f"{contributer.login}'s Punchcard"

    plot_commit_punchcard(commits, path, title)
