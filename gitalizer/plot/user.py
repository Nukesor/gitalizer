"""The main module for plotting user related graphs."""

import pandas as pd
from gitalizer.extensions import db
from gitalizer.models.commit import Commit
from gitalizer.models.repository import Repository
from gitalizer.models.contributer import Contributer


def get_user_repositories(name, repo):
    """Get all commits of repositories of an user."""
    contributer = db.session.query(Contributer) \
        .filter(Contributer.login == name) \
        .one()

    repository = db.session.query(Repository) \
        .filter(Repository.contributors.in_([contributer])) \
        .one()

    commits = db.session.query(Commit) \
        .filter(Commit.email.in_(contributer.emails)) \
        .filter(Commit.repository == repository) \
        .all()

    additions = [c.additions for c in commits]
    deletions = [c.deletions for c in commits]
    changes = [math.abs(c.additions - c.deletions) for c in commits]

    df = pd.DataFrame()
