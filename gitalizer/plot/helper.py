"""Helper for getting specific data sets."""

from gitalizer.extensions import db
from gitalizer.models.repository import Repository
from gitalizer.models.contributer import contributer_repositories


def get_user_repositories(contributer):
    """Get all commits of repositories of an user."""
    print(contributer)
    repositories = db.session.query(Repository) \
        .join(
            contributer_repositories,
            contributer_repositories.c.repository_url == Repository.clone_url,
        ) \
        .filter(contributer_repositories.c.contributer_login == contributer.login) \
        .all()

    return repositories
