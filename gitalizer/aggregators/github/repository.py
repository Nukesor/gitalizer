"""Data collection from Github."""

from datetime import datetime
from github import Repository as Github_Repository

from flask import current_app

from gitalizer.extensions import db, github
from gitalizer.models.contributer import Contributer
from gitalizer.models.repository import Repository
from gitalizer.aggregators.github.commit import get_commits
from gitalizer.aggregators.github.helper import get_commit_count


def get_repository(github_repo: Github_Repository):
    """Get all information from a single repository."""
    repository = db.session.query(Repository).get(github_repo.clone_url)
    if not repository:
        repository = Repository(github_repo.clone_url)
        db.session.add(repository)
        db.session.commit()

    # Skip repositories that are too big.
    contributors = github_repo.get_contributors()
    count = get_commit_count(contributors)

    current_time = datetime.now().strftime('%H:%M')
    limit = current_app.config['GITHUB_SKIP']
    if count >= limit:
        print(f'\n{current_time}: Skip {repository.clone_url}. It has more than {limit} commits.')
        return
    else:
        # Repository isn't too big, start to scan
        print(f'\n{current_time}: Started scan {repository.clone_url} with {count} commits.')

    # Register all contributors
    for user in contributors:
        contributer = db.session.query(Contributer).get(user.login)
        if not contributer:
            contributer = Contributer(user.login)
        contributer.repositories.append(repository)
        db.session.add(contributer)
    db.session.commit()

    commit_count = get_commits(github_repo, repository, contributer)

    time = datetime.fromtimestamp(github.github.rate_limiting_resettime)
    time = time.strftime("%H:%M")
    current_time = datetime.now().strftime('%H:%M')
    print(f'{current_time}: Scanned {repository.clone_url} with {commit_count} commits')
    print(f'{github.github.rate_limiting} of 5000 remaining. Reset at {time}')
