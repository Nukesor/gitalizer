"""The main module for plotting user related graphs."""
from datetime import timedelta

from .plotting import (
    MissingTimeComparison,
)


def plot_compare_employee_missing_time(contributors, repositories, path):
    """Plot a timeline with marked missing times."""
    delta = timedelta(days=364)
    contributor_names = [c.login for c in contributors]
    title = f"{', '.join(contributor_names)} Missing times"

    plotter = MissingTimeComparison(contributors, repositories, delta, path, title)
    plotter.run()
