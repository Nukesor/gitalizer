"""The main module for plotting user related graphs."""

import math
import pandas as pd
from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributer import Contributer
from gitalizer.plot.helper import get_user_repositories


def plot_user_repositories_changes(name):
    """Get all commits of repositories of an user."""
    contributer = db.session.query(Contributer) \
        .filter(Contributer.login.ilike(name)) \
        .one()

    repositories = get_user_repositories(contributer)
    for repository in repositories:
        plot_user_repository_changes(contributer, repository)


def plot_user_repository_changes(contributer, repo):
    """Plot the changes for a specific contributer and repository."""
    commits = db.session.query(Commit) \
        .filter(Commit.repository == repo) \
        .join(Email, Email.email == Commit.author_email) \
        .join(Contributer, Email.contributer_login == Contributer.login) \
        .filter(Contributer.login == contributer.login) \
        .all()
    if len(commits) < 20:
        return

    data = []
    for c in commits:
        time = c.time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if c.additions and c.deletions:
            data.append({
                'date': time,
                'additions': c.additions,
                'deletions': c.deletions,
                'changes': math.fabs(c.additions - c.deletions),
            })

    df = pd.DataFrame(data=data)
    df = df.sort_values(by='date')
    df = df.set_index('date')

    print(df)
