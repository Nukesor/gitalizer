"""Data collection from Github."""

from github import NamedUser
from datetime import datetime, timedelta

from gitalizer.models import Repository
from gitalizer.extensions import github, db
from gitalizer.aggregator.github.repository import get_github_repositories
from gitalizer.aggregator.github import call_github_function
from gitalizer.aggregator.threading import new_session


def get_friends_by_name(name: str):
    """Get all relevant Information about all friends of a specific user.."""
    user = call_github_function(github.github, 'get_user', [name])
    followers = call_github_function(user, 'get_followers', [])
    following = call_github_function(user, 'get_following', [])

    # Add all following and followed people into list
    # Then deduplicate the list as we have to hold the API call count as low as possible.
    user_list = [user]
    for follower in followers:
        user_list.append(follower)
    for followed in following:
        exists = filter(lambda x: x.login == followed.login, user_list)
        if len(list(exists)) == 0:
            user_list.append(followed)

    session = new_session()
    # Get all deduplicated github repositories
    repositories = []
    for user in user_list:
        print(f'Added repositories for user {user.login}:')
        get_user_repos(user, repositories, session)

    # Scan all repositories with a worker thread pool
    get_github_repositories(repositories)


def get_user_by_name(user: str):
    """Get a user by his login name."""
    user = call_github_function(github.github, 'get_user', [user])
    # Scan all repositories with a worker thread pool
    session = new_session()
    repos = get_user_repos(user, [], session)
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
