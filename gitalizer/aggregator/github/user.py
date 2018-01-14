"""Data collection from Github."""
import traceback
from flask import current_app

from gitalizer.models import Repository, Contributer
from gitalizer.extensions import github, sentry
from gitalizer.aggregator.github import call_github_function
from gitalizer.aggregator.parallel import new_session
from gitalizer.aggregator.parallel.manager import Manager


def get_friends_by_name(name: str):
    """Get all relevant Information about all friends of a specific user.."""
    user = call_github_function(github.github, 'get_user', [name])
    followers = call_github_function(user, 'get_followers')
    following = call_github_function(user, 'get_following')

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
#    for user in user_list:
#        print(user)
    sub_manager = Manager('github_repository', [])
    manager = Manager('github_contributer', user_list, sub_manager)
    manager.start()
    manager.run()


def get_user_by_name(user: str):
    """Get a user by his login name."""
    user = call_github_function(github.github, 'get_user', [user])
    # Get a new session to prevent spawning a db.session.
    # Otherwise we get problems as this session is used in each thread as well.
    sub_manager = Manager('github_repository', [])
    manager = Manager('github_contributer', [user.login], sub_manager)
    manager.start()
    manager.run()


def get_user_repos(user_login: str):
    """Get all relevant Information for a single user."""
    try:
        session = new_session()
        user = call_github_function(github.github, 'get_user', [user_login])
        owned = user.get_repos()
        starred = user.get_starred()
        repos_to_scan = []
        contributer = Contributer.get_contributer(user_login, session)
        user_too_big_message = {
            'message': f'User {user_login} has too many repositories',
            'error': 'Too big',
        }
        if contributer.too_big:
            return user_too_big_message

        owned_repos = 0
        while owned._couldGrow():
            owned_repos += 1
            # Debug messages to see that the repositories are still collected.
            if owned_repos % 100 == 0:
                current_app.logger.info(f'{owned_repos} owned repos for user {user_login}.')

            # The user is too big. Just drop him.
            if owned_repos > 5000:
                contributer.too_big = True
                session.add(contributer)
                session.commit()
                return user_too_big_message

            call_github_function(owned, '_grow', [])
        # Check own repositories. We assume that we are collaborating in those
        for repo in owned:
            # Don't scan the repo
            # - Add it if it's not yet added
            # - If we already scanned it in the last 24 hours
            if not Repository.should_scan(repo.clone_url, session):
                continue
            repos_to_scan.append(repo)

        starred_repos = 0
        while starred._couldGrow():
            starred_repos += 1
            # Debug messages to see that the repositories are still collected.
            if starred_repos % 100 == 0:
                current_app.logger.info(f'{starred_repos} starred repos for user {user_login}.')

            # The user is too big. Just drop him.
            if starred_repos > 5000:
                contributer.too_big = True
                session.add(contributer)
                session.commit(contributer)
                return user_too_big_message

            call_github_function(starred, '_grow', [])
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
            'message': f'Got repositories for {user.login}.',
            'tasks': [r.full_name for r in repos_to_scan],
        }
    except BaseException as e:
        # Catch any exception and print it, as we won't get any information due to threading otherwise.
        sentry.sentry.captureException()
        response = {
            'message': f'Error while getting repos for {user_login}:\n',
            'error': traceback.format_exc(),
        }
        pass
    return response
