"""Data collection from Github."""

from github import NamedUser

from gitalizer.extensions import github
from gitalizer.aggregators.github.repository import get_github_repositories


def get_friends(name: str):
    """Get all relevant Information about all friends of a specific user.."""
    user = github.github.get_user(name)
    followers = user.get_followers()
    following = user.get_following()

    # Add all following and followed people into list
    # Then deduplicate the list as we have to hold the API call count as low as possible.
    user_list = [user]
    for follower in followers:
        user_list.append(follower)
    for followed in following:
        exists = filter(lambda x: x.login == followed.login, user_list)
        if len(list(exists)) == 0:
            user_list.append(followed)

    # Get all deduplicated github repositories
    repositories = []
    for user in user_list:
        print(f'Added repositories for user {user.login}:')
        get_user_repos(user, repositories)

    # Scan all repositories with a worker thread pool
    get_github_repositories(repositories)


def get_user_by_name(user: str):
    """Get a user by his login name."""
    user = github.github.get_user(user)
    # Scan all repositories with a worker thread pool
    get_github_repositories(get_user_repos(user, []))


def get_user_repos(user: NamedUser, repos_to_scan):
    """Get all relevant Information for a single user."""
    owned_repos = user.get_repos()
    starred = user.get_starred()

    for repo in owned_repos:
        exists = filter(lambda x: x.clone_url == repo.clone_url, repos_to_scan)
        if len(list(exists)) == 0:
            repos_to_scan.append(repo)

    for star in starred:
        # Check if user contributed to this repo.
        contributed = list(filter(lambda x: x.login == user.login, star.get_contributors()))
        if len(contributed) == 0:
            break
        exists = filter(lambda x: x.clone_url == star.clone_url, repos_to_scan)
        if len(list(exists)) == 0:
            repos_to_scan.append(star)
    return repos_to_scan
