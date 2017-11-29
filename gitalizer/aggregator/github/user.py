"""Data collection from Github."""

from github import NamedUser
from datetime import datetime, timedelta

from gitalizer.models import Repository
from gitalizer.extensions import github
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
    repos = {}
    for user in user_list:
        print(f'Added repositories for user {user.login}:')
        get_user_repos(user, repos, session)

    repos = [repos[k] for k in repos]
    # Scan all repositories with a worker thread pool
    get_github_repositories(repos)


def get_user_by_name(user: str):
    """Get a user by his login name."""
    user = call_github_function(github.github, 'get_user', [user])
    # Get a new session to prevent spawning a db.session.
    # Otherwise we get problems as this session is used in each thread as well.
    session = new_session()
    repos = {}
    repos = get_user_repos(user, repos, session)
    repos = [repos[k] for k in repos]
    # Scan all repositories with a worker thread pool
    get_github_repositories(repos)


def get_user_repos(user: NamedUser, repos_to_scan, session):
    """Get all relevant Information for a single user."""
    owned_repos = call_github_function(user, 'get_repos', [])
    starred = call_github_function(user, 'get_starred', [])

    # Check own repositories. We assume that we are collaborating in those
    for repo in owned_repos:
        # Don't scan the repo
        # - Add it if it's not yet added
        # - If we already scanned it in the last 24 hours
        if repo.clone_url in repos_to_scan or \
                should_not_scan_repository(repo.clone_url, session):
            continue

        repos_to_scan[repo.clone_url] = repo

    # Check stars. In here we need to check if the user collaborated in the repo.
    for star in starred:
        # Don't scan the repo
        # - Add it if it's not yet added
        # - If we already scanned it in the last 24 hours
        # - If the user is a collaborator in this repo
        if star.clone_url in repos_to_scan or \
                should_not_scan_repository(star.clone_url, session) or \
                not call_github_function(star, 'has_in_collaborators', [user]):
            continue

        repos_to_scan[star.clone_url] = star

    return repos_to_scan


def should_not_scan_repository(clone_url: str, session):
    """Check if the repo has been updated in the last hour.

    If that is the case, we want to skip it.
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=24)
    repo = session.query(Repository) \
        .filter(Repository.clone_url == clone_url) \
        .filter(Repository.completely_scanned == True) \
        .filter(Repository.updated_at >= one_hour_ago) \
        .one_or_none()
    if repo:
        return True
    return False
