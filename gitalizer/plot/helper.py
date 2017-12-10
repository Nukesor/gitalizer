"""Helper for getting specific data sets."""
import matplotlib.pyplot as plt

from gitalizer.extensions import db
from gitalizer.models.repository import Repository
from gitalizer.models.contributer import contributer_repositories


def get_user_repositories(contributer):
    """Get all commits of repositories of an user."""
    repositories = db.session.query(Repository) \
        .join(
            contributer_repositories,
            contributer_repositories.c.repository_url == Repository.clone_url,
        ) \
        .filter(contributer_repositories.c.contributer_login == contributer.login) \
        .all()

    return repositories


def plot_figure(path, ax):
    """Save a plot to a graph."""
    plt.xticks(rotation=30)

    plt.figure(figsize=(20, 10))
    fig = ax.get_figure()
    fig.savefig(path)

    plt.close(fig)
