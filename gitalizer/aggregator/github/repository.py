"""Data collection from Github."""
from time import sleep
from random import randrange
from datetime import datetime
from github import GithubException
from raven import breadcrumbs
from pygit2 import GitError
from gitalizer.helpers.config import config

from gitalizer.extensions import github, sentry, logger
from gitalizer.models.repository import Repository
from gitalizer.helpers.parallel import new_session
from gitalizer.helpers.parallel.manager import Manager
from gitalizer.helpers.parallel.messages import error_message
from gitalizer.aggregator.git.commit import CommitScanner
from gitalizer.aggregator.git.repository import get_git_repository, delete_git_repository
from gitalizer.aggregator.github import (
    call_github_function,
    get_github_object,
)


def get_github_repository_by_owner_name(owner: str, name: str):
    """Get a repository by it's owner and name."""
    full_name = f'{owner}/{name}'
    response = get_github_repository(full_name)
    logger.info(response['message'])
    if 'error' in response:
        logger.error(response['error'])


def get_github_repository_users(full_name: str):
    """Get all collaborators of a repository."""
    repo = call_github_function(github.github, 'get_repo', [full_name])
    collaborators = call_github_function(repo, 'get_collaborators')
    while collaborators._couldGrow():
        call_github_function(collaborators, '_grow')

    collaborator_list = [c.login for c in collaborators]

    sub_manager = Manager('github_repository', [])
    manager = Manager('github_contributor', collaborator_list, sub_manager)
    manager.start()
    manager.run()


def get_github_repository(full_name: str):
    """Get all information from a single repository."""
    try:
        session = new_session()
        # Sleep for a random time to avoid hitting the abuse detection.
        sleeptime = randrange(1, 15)
        sleep(sleeptime)

        github_repo = call_github_function(github.github, 'get_repo',
                                           [full_name], {'lazy': False})

        repository = Repository.get_or_create(
            session,
            github_repo.ssh_url,
            name=github_repo.name,
            full_name=github_repo.full_name,
        )

        if repository.broken:
            return {'message': f'Skip broken repo {github_repo.ssh_url}'}
        elif github_repo.size > int(config['aggregator']['max_repository_size']):
            repository.too_big = True
            session.add(repository)
            session.commit()
            sentry.captureMessage(f'Repo filesize too big', level='info',
                                  extra={'repo': repository.clone_url})

            return {'message': f'Repo too big (filesize): {github_repo.ssh_url}'}

        current_time = datetime.now().strftime('%H:%M')

        owner = get_github_object(github_repo, 'owner')
        git_repo = get_git_repository(
            github_repo.ssh_url,
            owner.login,
            github_repo.name,
        )
        scanner = CommitScanner(git_repo, session, github_repo)
        commit_count = scanner.scan_repository()

        breadcrumbs.record(
            data={'action': 'Commits scanned. Set repo metadata and debug output'},
            category='info',
        )

        repository = session.query(Repository).get(github_repo.ssh_url)
        rate = github.github.get_rate_limit().core
        time = rate.reset.strftime("%H:%M")
        current_time = datetime.now().strftime('%H:%M')

        message = f'{current_time}: '
        message += f'Scanned {repository.clone_url} with {commit_count} commits.\n'
        message += f'{rate.remaining} of 5000 remaining. Reset at {time}\n'

        response = {'message': message}

        repository.updated_at = datetime.now()
        session.add(repository)
        session.commit()

    except GithubException as e:
        # 451: Access denied. Repository probably gone private.
        # 404: User or repository just got deleted
        if e.status == 451 or e.status == 404:
            repository = session.query(Repository) \
                .filter(Repository.full_name == full_name) \
                .one_or_none()

            if repository:
                repository.broken = True
                session.add(repository)
                session.commit()
            response = {'message': 'Repository access blocked.'}
        # Catch any other GithubException
        else:
            sentry.captureException()
            response = error_message('Error in get_repository:\n')

        pass

    except (GitError, UnicodeDecodeError):
        response = error_message('Error in get_repository:\n')
        pass

    except BaseException:
        # Catch any exception and print it, as we won't get any information due to threading otherwise.
        sentry.captureException()
        response = error_message('Error in get_repository:\n')
        pass

    finally:
        if 'owner' in locals() and 'github_repo' in locals():
            delete_git_repository(owner.login, github_repo.name)
        session.close()

    return response
