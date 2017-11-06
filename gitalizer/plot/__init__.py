"""The main module for plotting graphs."""

from .user import plot_user_repositories_changes


def plot_user(owner):
    """Plot all user related graphs."""
    plot_user_repositories_changes(owner)
