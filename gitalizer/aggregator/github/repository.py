"""Data collection from Github."""

from datetime import datetime
from multiprocessing import Pool
from flask import current_app
from github import Repository as Github_Repository

from gitalizer.extensions import db, github
from gitalizer.models.repository import Repository
from gitalizer.aggregator.git.commit import CommitScanner
from gitalizer.aggregator.git.repository import get_git_repository


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
    github_repo = github.github.get_repo(full_name)
    get_github_repository(github_repo)


def get_github_repository(github_repo: Github_Repository):
    """Get all information from a single repository."""
    repository = db.session.query(Repository).get(github_repo.clone_url)
    if not repository:
        repository = Repository(github_repo.clone_url, github_repo.name)
        db.session.add(repository)
    db.session.commit()

    # Handle github_repo forks
    for fork in github_repo.get_forks():
        fork_repo = db.session.query(Repository).get(fork.clone_url)
        if not fork_repo:
            fork_repo = Repository(fork.clone_url, fork.name)
        fork_repo.parent = repository
        db.session.add(fork_repo)
    db.session.commit()

    current_time = datetime.now().strftime('%H:%M')
    print(f'\n{current_time}: Started scan {repository.clone_url}.')

    git_repo = get_git_repository(
        github_repo.clone_url,
        github_repo.owner.login,
        github_repo.name,
    )
    scanner = CommitScanner(git_repo, repository, github_repo)
    commit_count = scanner.scan_repository()

    time = datetime.fromtimestamp(github.github.rate_limiting_resettime)
    time = time.strftime("%H:%M")
    current_time = datetime.now().strftime('%H:%M')
    print(f'{current_time}: Scanned {repository.clone_url} with {commit_count} commits')
    print(f'{github.github.rate_limiting} of 5000 remaining. Reset at {time}')
