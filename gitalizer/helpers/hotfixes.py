"""Clean stuff from db, which occured through bugs."""
from flask import current_app
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from gitalizer.extensions import db, github
from gitalizer.models import (
    Repository,
    Commit,
    contributer_repository,
    commit_repository,
)
from gitalizer.aggregator.parallel import new_session
from gitalizer.aggregator.parallel.manager import Manager
from gitalizer.aggregator.github.user import check_fork
from gitalizer.aggregator.github import (
    call_github_function,
)


def clean_db():
    """Clean stuff."""
    print("Removing commits from fork repos.")
    all_repositories = db.session.query(Repository) \
        .filter(Repository.fork.is_(True)) \
        .filter(Repository.commits != None) \
        .options(joinedload(Repository.commits)) \
        .all()

    print(f'Found {len(all_repositories)}')
    repositories_count = 0
    for repository in all_repositories:
        repository.commits = []
        db.session.add(repository)
        repositories_count += 1
        if repositories_count % 100 == 0:
            print(f'Removed {repositories_count}')
            db.session.commit()

    print("Remove unattached commits")
    db.session.query(Commit) \
        .filter(Commit.repositories == None) \
        .delete()
    db.session.commit()


def complete_data():
    """Clean stuff."""
    complete_repos()


def complete_repos():
    """Complete unfinished repsitories."""
    print("Get unfinished or out of date repositories.")
    timeout_threshold = datetime.utcnow() - current_app.config['REPOSITORY_RESCAN_TIMEOUT']
    session = new_session()

    repos = session.query(Repository) \
        .filter(Repository.fork.is_(False)) \
        .filter(Repository.broken.is_(False)) \
        .filter(Repository.too_big.is_(False)) \
        .filter(or_(
            Repository.completely_scanned.is_(False),
            Repository.updated_at <= timeout_threshold,
        )) \
        .all()
    print(f'Found {len(repos)}')

    full_names = [r.full_name for r in repos]
    repo_count = 0
    repos_to_scan = set()
    for name in full_names:
        repos_to_scan.add(name)
        repo_count += 1
        if repo_count % 100 == 0 or repo_count == len(repos):
            print(f'Get batch {repo_count}')
            manager = Manager('github_repository', repos_to_scan)
            manager.start()
            manager.run()
            repos_to_scan = set()

    manager = Manager('github_repository', repos_to_scan)
    manager.start()
    manager.run()

    db.session.commit()
