"""Data collection from Github."""
import traceback
from time import sleep
from random import randrange
from datetime import datetime
from github import GithubException
from raven import breadcrumbs
from pygit2 import GitError

from gitalizer.extensions import github, sentry
from gitalizer.models.repository import Repository
from gitalizer.aggregator.parallel import new_session
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
    print(response['message'])
    if 'error' in response:
        print(response['error'])


def get_github_repository(full_name: str):
    """Get all information from a single repository."""
    try:
        session = new_session()
        # Sleep for a random time to avoid hitting the abuse detection.
        sleeptime = randrange(1, 15)
        sleep(sleeptime)

        github_repo = call_github_function(github.github, 'get_repo',
                                           [full_name], {'lazy': False})
        repository = session.query(Repository).get(github_repo.clone_url)
        if not repository:
            repository = Repository(github_repo.clone_url, github_repo.name)
            session.add(repository)
            session.commit()
        elif repository.broken:
            return {'message': f'Skip broken repo {github_repo.clone_url}'}

        # Handle github_repo forks
        for fork in call_github_function(github_repo, 'get_forks'):
            fork_repo = session.query(Repository).get(fork.clone_url)
            if not fork_repo:
                fork_repo = Repository(fork.clone_url, fork.name)
            fork_repo.parent = repository
            session.add(fork_repo)
        session.commit()

        current_time = datetime.now().strftime('%H:%M')

        owner = get_github_object(github_repo, 'owner')
        git_repo = get_git_repository(
            github_repo.clone_url,
            owner.login,
            github_repo.name,
        )
        scanner = CommitScanner(git_repo, session, github_repo)
        commit_count = scanner.scan_repository()
        session.commit()

        breadcrumbs.record(
            data={'action': 'Commits scanned. Set repo metadata and debug output'},
            category='info',
        )

        repository = session.query(Repository).get(github_repo.clone_url)
        rate = github.github.get_rate_limit().rate
        time = rate.reset.strftime("%H:%M")
        current_time = datetime.now().strftime('%H:%M')

        message = f'{current_time}: '
        message += f'Scanned {repository.clone_url} with {commit_count} commits.\n'
        message += f'{rate.remaining} of 5000 remaining. Reset at {time}\n'

        response = {
            'message': message,
        }

        repository.updated_at = datetime.now()
        session.add(repository)
        session.commit()

    except GithubException as e:
        # Catch a Github exception.
        sentry.sentry.captureException()
        response = {
            'message': 'Error in get repository:\n',
            'error': traceback.format_exc(),
        }
        pass

    except GitError as e:
        repository.broken = True
        session.add(repository)
        session.commit()
        response = {
            'message': 'Error in get repository:\n',
            'error': traceback.format_exc(),
        }

    except BaseException as e:
        # Catch any exception and print it, as we won't get any information due to threading otherwise.
        sentry.sentry.captureException()
        response = {
            'message': f'Error in {github_repo.clone_url}:\n',
            'error': traceback.format_exc(),
        }
        pass
    finally:
        if 'owner' in locals() and 'github_repo' in locals():
            delete_git_repository(owner.login, github_repo.name)
        session.close()
    return response
