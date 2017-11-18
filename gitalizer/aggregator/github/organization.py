"""Data collection from Github."""

from github import NamedUser
from datetime import datetime, timedelta

from gitalizer.extensions import github
from gitalizer.models import Repository, Contributer, Organization
from gitalizer.aggregator.github.repository import get_github_repositories
from gitalizer.aggregator.github import call_github_function
from gitalizer.aggregator.threading import new_session


def get_github_organizations(user: str):
    """Refresh all user organizations."""
    # Get a new session to prevent spawning a db.session.
    # Otherwise we get problems as this session is used in each thread as well.
    session = new_session()

    contributers = session.query(Contributer).all()
    for contributer in contributers:
        if contributer.last_check > datetime.now() - timedelta(days=2):
            continue
        github_user = call_github_function(github.github, 'get_user',
                                           [contributer.login])

        github_orgs = call_github_function(github_user, 'get_orgs', [])
        for org in github_orgs:
            organization = Organization.get_organization(org.login, org.url)
            contributer.append(organization)

    repos = get_user_repos(user, [], session)
    session.close()
    # Scan all repositories with a worker thread pool
    get_github_repositories(repos)


def get_user_repos(user: NamedUser, repos_to_scan: list, session):
    """Get all relevant Information for a single user."""
    owned_repos = call_github_function(user, 'get_repos', [])
    starred = call_github_function(user, 'get_starred', [])

    for repo in owned_repos:
        if not should_scan_repository(repo.clone_url, session):
            continue
        exists = filter(lambda x: x.clone_url == repo.clone_url, repos_to_scan)
        if len(list(exists)) == 0:
            repos_to_scan.append(repo)

    for star in starred:
        if not should_scan_repository(star.clone_url, session):
            continue
        # Check if user contributed to this repo.
        contributed = list(filter(lambda x: x.login == user.login, star.get_contributors()))
        if len(contributed) == 0:
            break
        exists = filter(lambda x: x.clone_url == star.clone_url, repos_to_scan)
        if len(list(exists)) == 0:
            repos_to_scan.append(star)
    return repos_to_scan


def should_scan_repository(clone_url: str, session):
    """Check if the repo has been updated in the last hour.

    If that is the case, we want to skip it.
    """
    one_hour_ago = datetime.now() - timedelta(hours=24)
    repo = session.query(Repository) \
        .filter(Repository.clone_url == clone_url) \
        .filter(Repository.completely_scanned == True) \
        .filter(Repository.updated_at >= one_hour_ago) \
        .one_or_none()
    if repo:
        return False
    return True
