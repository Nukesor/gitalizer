"""Data collection from Github."""

from github import NamedUser

from gitalizer.models import Repository
from gitalizer.extensions import github
from gitalizer.aggregator.github import call_github_function
from gitalizer.aggregator.parallel import new_session
from gitalizer.aggregator.parallel.manager import Manager


def get_friends_by_name(name: str):
    """Get all relevant Information about all friends of a specific user.."""
    user = call_github_function(github.github, 'get_user', [name])
    followers = call_github_function(user, 'get_followers', [])
    following = call_github_function(user, 'get_following', [])

    # Add all following and followed people into list
    # Deduplicate the list as we have to make as few API calls as possible.
    user_list = [user]
    for follower in followers:
        user_list.append(follower)
    for followed in following:
        exists = filter(lambda x: x.login == followed.login, user_list)
        if len(list(exists)) == 0:
            user_list.append(followed)

    user_list = [u.login for u in user_list]
    sub_manager = Manager('github_repository', [])
    manager = Manager('github_contributer', user_list, sub_manager)
    manager.run()


def get_user_by_name(user: str):
    """Get a user by his login name."""
    user = call_github_function(github.github, 'get_user', [user])
    # Get a new session to prevent spawning a db.session.
    # Otherwise we get problems as this session is used in each thread as well.
    sub_manager = Manager('github_repository', [])
    manager = Manager('github_contributer', [user.login], sub_manager)
    manager.run()


def get_user_repos(user_login: str):
    """Get all relevant Information for a single user."""
    session = new_session()
    user = call_github_function(github.github, 'get_user', [user_login])
    owned_repos = call_github_function(user, 'get_repos', [])
    starred = call_github_function(user, 'get_starred', [])

    repos_to_scan = []
    # Check own repositories. We assume that we are collaborating in those
    for repo in owned_repos:
        # Don't scan the repo
        # - Add it if it's not yet added
        # - If we already scanned it in the last 24 hours
        if not Repository.should_scan(repo.clone_url, session):
            continue
        repos_to_scan.append(repo.clone_url)

    # Check stars. In here we need to check if the user collaborated in the repo.
    for star in starred:
        # Don't scan the repo
        # - Add it if it's not yet added
        # - If we already scanned it in the last 24 hours
        # - If the user is a collaborator in this repo
        if not Repository.should_scan(star.clone_url, session) or \
                not call_github_function(star, 'has_in_collaborators', [user]):
            continue

        repos_to_scan.append(star)

    response = {
        'message': f'Repositories for {user.login} gotten.',
        'tasks': repos_to_scan,
    }
    return response
