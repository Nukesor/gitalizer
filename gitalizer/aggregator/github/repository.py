"""Data collection from Github."""

import sys
from flask import current_app
from datetime import datetime, timedelta
from multiprocessing import Pool
from github import Repository as Github_Repository

from gitalizer.extensions import db, github
from gitalizer.models.repository import Repository
from gitalizer.aggregator.git.commit import CommitScanner
from gitalizer.aggregator.git.repository import get_git_repository
from gitalizer.aggregator.github import (
    call_github_function,
    get_github_object,
)


def get_github_repositories(repositories: list):
    """Get multiple github repositories.

    We use a thread pool and one worker per repository.
    """
    print(f'Scanning {len(repositories)} repositories')
    pool = Pool(current_app.config['GIT_SCAN_THREADS'])
    pool.map(get_github_repository, repositories)


def get_github_repository_by_owner_name(owner: str, name: str):
    """Get a repository by it's owner and name."""
    full_name = f'{owner}/{name}'
    github_repo = call_github_function(github.github, 'get_repo', [full_name])
    get_github_repository(github_repo)


def get_github_repository(github_repo: Github_Repository):
    """Get all information from a single repository."""
    try:
        repository = db.session.query(Repository).get(github_repo.clone_url)
        if not repository:
            repository = Repository(github_repo.clone_url, github_repo.name)
        repository.updated_at = datetime.now()
        db.session.add(repository)
        db.session.commit()

        # Handle github_repo forks
        for fork in call_github_function(github_repo, 'get_forks', []):
            fork_repo = db.session.query(Repository).get(fork.clone_url)
            if not fork_repo:
                fork_repo = Repository(fork.clone_url, fork.name)
            fork_repo.parent = repository
            db.session.add(fork_repo)
        db.session.commit()

        current_time = datetime.now().strftime('%H:%M')
        print(f'{current_time}: Started scan {repository.clone_url}.')

        owner = get_github_object(github_repo, 'owner')
        git_repo = get_git_repository(
            github_repo.clone_url,
            owner.login,
            github_repo.name,
        )
        scanner = CommitScanner(git_repo, repository, github_repo)
        commit_count = scanner.scan_repository()

        repository = db.session.query(Repository).get(github_repo.clone_url)
        rate = github.github.get_rate_limit().rate
        time = rate.reset.strftime("%H:%M")
        current_time = datetime.now().strftime('%H:%M')
        print(f'{current_time}: Scanned {repository.clone_url} with {commit_count} commits')
        print(f'{rate.remaining} of 5000 remaining. Reset at {time}\n')
        db.session.commit()
        db.session.close()
    except BaseException as e:
        # Catch any exception and print it, as we won't get any information due to threading otherwise.
        print(e)
        raise e


def should_scan_repository(clone_url: str):
    """Check if the repo has been updated in the last hour.

    If that is the case, we want to skip it.
    """
    one_hour_ago = datetime.now() - timedelta(hours=24)
    repo = db.session.query(Repository) \
        .filter(Repository.clone_url == clone_url) \
        .filter(Repository.completely_scanned == True) \
        .filter(Repository.updated_at >= one_hour_ago) \
        .one_or_none()
    if repo:
        return False
    return True
