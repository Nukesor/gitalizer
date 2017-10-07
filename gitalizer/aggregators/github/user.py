"""Data collection from Github."""

from github import NamedUser

from gitalizer.extensions import github
from gitalizer.aggregators.github.repository import get_github_repository


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

    for user in user_list:
        print(f'Start scanning user {user.login}:')
        get_user(user)


def get_user_by_name(user: str):
    """Get a user by his login name."""
    user = github.github.get_user(user)
    get_user(user)


def get_user(user: NamedUser):
    """Get all relevant Information for a single user."""
    repos = user.get_repos()
    starred = user.get_starred()

    for star in starred:
        # Check if user contributed to this repo.
        contributed = list(filter(lambda x: x.login == user.login, star.get_contributors()))
        if len(contributed) == 0:
            break
        get_github_repository(star)

    for repo in repos:
        get_github_repository(repo)
