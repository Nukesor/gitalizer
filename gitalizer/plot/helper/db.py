"""DB helper for plotting."""
from sqlalchemy import or_
from datetime import timedelta, datetime

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit, commit_repository
from gitalizer.models.repository import Repository
from gitalizer.models.contributer import Contributer, contributer_repository


def get_user_repositories(contributer):
    """Get all commits of repositories of an user."""
    repositories = db.session.query(Repository) \
        .join(
            contributer_repository,
            contributer_repository.c.repository_clone_url == Repository.clone_url,
        ) \
        .filter(contributer_repository.c.contributer_login == contributer.login) \
        .all()

    return repositories


def get_user_commits(contributer, delta=None):
    """Get ALL commits of a contributer in a given timespan."""
    if delta is None:
        delta = timedelta(days=99*365)
    time_span = datetime.now() - delta
    commits = db.session.query(Commit) \
        .filter(Commit.commit_time >= time_span) \
        .join(Email, or_(
            Email.email == Commit.author_email_address,
            Email.email == Commit.committer_email_address,
        )) \
        .join(Contributer, Email.contributer_login == contributer.login) \
        .filter(Contributer.login == contributer.login) \
        .order_by(Commit.commit_time.asc()) \
        .all()

    return commits


def get_user_commits_from_repositories(contributer, repositories, delta=None):
    """Get ALL commits of a contributer in a given timespan."""
    if delta is None:
        delta = timedelta(days=99*365)
    time_span = datetime.now() - delta

    conditions = []
    full_names = [r.full_name for r in repositories]
    print(full_names)
    for name in full_names:
        conditions.append(Repository.full_name.ilike(name))

    commits = db.session.query(Commit) \
        .filter(Commit.commit_time >= time_span) \
        .join(Email, or_(
            Email.email == Commit.author_email_address,
            Email.email == Commit.committer_email_address,
        )) \
        .join(Contributer, Email.contributer_login == Contributer.login) \
        .join(
            commit_repository,
            commit_repository.c.commit_sha == Commit.sha,
        ) \
        .join(Repository, commit_repository.c.repository_clone_url == Repository.clone_url) \
        .filter(Contributer.login == contributer.login) \
        .order_by(Commit.commit_time.asc()) \
        .all()
        #.filter(or_(*conditions)) \
        #.filter(Repository.full_name.in_(full_names)) \

    return commits
