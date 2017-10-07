"""Data collection from Github."""

from datetime import datetime
from multiprocessing import Pool
from flask import current_app
from github import Repository as Github_Repository

from gitalizer.extensions import db, github
from gitalizer.models.repository import Repository
from gitalizer.aggregators.git.commit import scan_repository
from gitalizer.aggregators.git.repository import get_git_repository


def get_github_repositories(repositories):
    """Get multiple github repositories.

    We use a thread pool and one worker per repository.
    """
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
        repository = Repository(github_repo.clone_url)
        db.session.add(repository)
        db.session.commit()

    current_time = datetime.now().strftime('%H:%M')
    print(f'\n{current_time}: Started scan {repository.clone_url}.')

    git_repo = get_git_repository(
        github_repo.clone_url,
        github_repo.owner.login,
        github_repo.name,
    )
    commit_count = scan_repository(git_repo, repository, github_repo)

    time = datetime.fromtimestamp(github.github.rate_limiting_resettime)
    time = time.strftime("%H:%M")
    current_time = datetime.now().strftime('%H:%M')
    print(f'{current_time}: Scanned {repository.clone_url} with {commit_count} commits')
    print(f'{github.github.rate_limiting} of 5000 remaining. Reset at {time}')
