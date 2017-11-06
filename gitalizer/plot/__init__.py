"""The main module for plotting graphs."""

import os
from .user import plot_user_repositories_changes


def plot_user(owner):
    """Plot all user related graphs."""
    plot_dir = 'plots'
    if not os.path.exists(plot_dir):
        os.mkdir(plot_dir)

    user_dir = os.path.join(plot_dir, owner.lower())
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)

    plot_user_repositories_changes(owner, user_dir)
