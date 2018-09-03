"""DB helper for plotting."""
from sqlalchemy import or_
from datetime import timedelta, datetime

from gitalizer.models.email import Email
from gitalizer.models.commit import Commit, commit_repository
from gitalizer.models.repository import Repository
from gitalizer.models.contributor import Contributor, contributor_repository


def get_user_repositories(contributor, session):
    """Get all commits of repositories of an user."""
    repositories = session.query(Repository) \
        .join(
            contributor_repository,
            contributor_repository.c.repository_clone_url == Repository.clone_url,
        ) \
        .filter(contributor_repository.c.contributor_login == contributor.login) \
        .all()

    return repositories


def get_user_commits(contributor, session=None, delta=None):
    """Get ALL commits of a contributor in a given timespan."""
    if delta is None:
        delta = timedelta(days=99*365)

    time_span = datetime.now() - delta
    commits = session.query(Commit) \
        .filter(Commit.commit_time >= time_span) \
        .join(Email, or_(
            Email.email == Commit.author_email_address,
            Email.email == Commit.committer_email_address,
        )) \
        .join(Contributor, Email.contributor_login == contributor.login) \
        .filter(Contributor.login == contributor.login) \
        .order_by(Commit.commit_time.asc()) \
        .all()

    return commits


def get_user_commits_from_repositories(contributor, repositories, session, delta=None):
    """Get ALL commits of a contributor in a given timespan."""
    if delta is None:
        delta = timedelta(days=99*365)
    time_span = datetime.now() - delta

    full_names = [r.full_name for r in repositories]

    commits = session.query(Commit) \
        .filter(Commit.commit_time >= time_span) \
        .join(Email, or_(
            Email.email == Commit.author_email_address,
            Email.email == Commit.committer_email_address,
        )) \
        .join(Contributor, Email.contributor_login == Contributor.login) \
        .join(
            commit_repository,
            commit_repository.c.commit_sha == Commit.sha,
        ) \
        .join(Repository, commit_repository.c.repository_clone_url == Repository.clone_url) \
        .filter(Repository.full_name.in_(full_names)) \
        .filter(Contributor.login == contributor.login) \
        .order_by(Commit.commit_time.asc()) \
        .all()

    return commits
