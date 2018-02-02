"""Data collection from Github."""
import traceback
from flask import current_app
from datetime import datetime

from gitalizer.models import Repository, Contributer
from gitalizer.extensions import github, sentry, db
from gitalizer.aggregator.github import call_github_function, get_github_object
from gitalizer.aggregator.parallel import new_session
from gitalizer.aggregator.parallel.manager import Manager
from gitalizer.aggregator.parallel.messages import (
    user_too_big_message,
    user_up_to_date_message,
)


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

    user_logins = [u.login for u in user_list]
#    for user in user_list:
#        print(user)
    sub_manager = Manager('github_repository', [])
    manager = Manager('github_contributer', user_logins, sub_manager)
    manager.start()
    manager.run()

    for login in user_logins:
        contributer = db.session.query(Contributer).get(login)
        if not contributer.too_big:
            contributer.last_full_scan = datetime.utcnow()
            db.session.add(contributer)
    db.session.commit()


def get_user_by_login(login: str):
    """Get a user by his login name."""
    user = call_github_function(github.github, 'get_user', [login])
    sub_manager = Manager('github_repository', [])
    manager = Manager('github_contributer', [user.login], sub_manager)
    manager.start()
    manager.run()

    contributer = db.session.query(Contributer).get(login)
    contributer.last_full_scan = datetime.utcnow()
    db.session.add(contributer)
    db.session.commit()


def get_user_repos(user_login: str, skip=True):
    """Get all relevant Information for a single user."""
    try:
        session = new_session()
        contributer = Contributer.get_contributer(user_login, session, True)
        # Checks for already scanned users.
        if not contributer.should_scan():
            return user_up_to_date_message(user_login)
        if contributer.too_big:
            return user_too_big_message(user_login)

        user = call_github_function(github.github, 'get_user', [user_login])
        owned = user.get_repos()
        starred = user.get_starred()
        repos_to_scan = set()

        # Prefetch all owned repositories
        user_too_big = False
        owned_repos = 0
        while False and owned._couldGrow() and not user_too_big:
            owned_repos += 1
            call_github_function(owned, '_grow')

            # Debug messages to see that the repositories are still collected.
            if owned_repos % 100 == 0:
                current_app.logger.info(f'{owned_repos} owned repos for user {user_login}.')

            # The user is too big. Just drop him.
            if skip and owned_repos > current_app.config['GITHUB_USER_SKIP_COUNT']:
                user_too_big = True

        # Prefetch all starred repositories
        starred_repos = 0
        while starred._couldGrow() and not user_too_big:
            starred_repos += 1
            call_github_function(starred, '_grow')
            # Debug messages to see that the repositories are still collected.
            if starred_repos % 100 == 0:
                current_app.logger.info(f'{starred_repos} starred repos for user {user_login}.')

            # The user is too big. Just drop him.
            if skip and starred_repos > current_app.config['GITHUB_USER_SKIP_COUNT']:
                user_too_big = True

        # User has too many repositories. Flag him and return
        if user_too_big:
            contributer.too_big = True
            session.add(contributer)
            session.commit()
            return user_too_big_message(user_login)

        # Check own repositories. We assume that we are collaborating in those
        for github_repo in owned:
            repository = Repository.get_or_create(
                session,
                github_repo.clone_url,
                name=github_repo.name,
                full_name=github_repo.full_name,
            )
            if github_repo.fork and not repository.is_invalid():
                check_fork(github_repo, session, repository,
                           repos_to_scan, user_login)
            session.add(repository)

            if not repository.should_scan():
                continue

            session.commit()
            repos_to_scan.add(github_repo.full_name)

        # Check stars and if the user collaborated to them.
        for github_repo in starred:
            repository = Repository.get_or_create(
                session,
                github_repo.clone_url,
                name=github_repo.name,
                full_name=github_repo.full_name,
            )

            if github_repo.fork and not repository.is_invalid():
                check_fork(github_repo, session, repository,
                           repos_to_scan, user_login)
            session.add(repository)

            if not repository.should_scan():
                continue

            repos_to_scan.add(github_repo.full_name)

        session.commit()

        rate = github.github.get_rate_limit().rate
        message = f'Got repositories for {user.login}. '
        message += f'{user.login}. {rate.remaining} of 5000 remaining.'
        response = {
            'message': message,
            'tasks': list(repos_to_scan),
        }
    except BaseException as e:
        # Catch any exception and print it, as we won't get any information due to threading otherwise.
        sentry.sentry.captureException()
        response = {
            'message': f'Error while getting repos for {user_login}:\n',
            'error': traceback.format_exc(),
        }
        pass
    finally:
        session.close()

    return response


def check_fork(github_repo, session, repository, scan_list, user_login=None):
    """Handle github_repo forks."""
    # We already scanned this repository and only need to check
    # if it or its parent should be scanned
    if repository.completely_scanned:
        # Its a fork, check if the parent needs to be scanned
        if repository.fork:
            if repository.parent.should_scan():
                scan_list.add(github_repo.parent.full_name)
        # Its no fork just skip and return
        else:
            return

    # We don't know the repository yet.
    # Create the parent and check if it is a valid fork
    get_github_object(github_repo, 'parent')
    parent_repository = Repository.get_or_create(
        session,
        github_repo.parent.clone_url,
        name=github_repo.parent.name,
        full_name=github_repo.parent.full_name,
    )

    # If the names are identical it's likely not spite/hate fork.
    if github_repo.parent.name == github_repo.name:
        # Set the parent on the forked repository
        if not repository.parent:
            repository.parent = parent_repository

        # Mark the repository as a fork and scan the parent.
        repository.fork = True
        if parent_repository.should_scan():
            scan_list.add(parent_repository.full_name)

    session.add(repository)
