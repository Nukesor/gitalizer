"""Clean stuff from db, which occured through bugs."""
from flask import current_app
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from gitalizer.extensions import db, github
from gitalizer.models import Repository, Commit
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
    print("Get repos with missing full_name.")
    repos = db.session.query(Repository) \
        .filter(Repository.full_name.is_(None)) \
        .all()

    print(f'Found {len(repos)}')

    for repo in repos:
        name_parts = repo.clone_url.rsplit('/', 2)
        owner = name_parts[1]
        name = name_parts[2].rsplit('.', 1)[0]
        full_name = f'{owner}/{name}'
        repo.name = name
        repo.full_name = full_name
        db.session.add(repo)

    db.session.commit()

    print("Get unfinished or out of date repositories.")
    timeout_threshold = datetime.utcnow() - current_app.config['REPOSITORY_RESCAN_TIMEOUT']

    repos = db.session.query(Repository) \
        .filter(Repository.fork.is_(False)) \
        .filter(Repository.broken.is_(False)) \
        .filter(or_(
            Repository.completely_scanned.is_(False),
            Repository.updated_at <= timeout_threshold,
        )) \
        .options(joinedload(Repository.parent)) \
        .all()
    print(f'Found {len(repos)}')

    repo_count = 0
    repos_to_scan = set()
    for repo in repos:
        github_repo = call_github_function(github.github, 'get_repo',
                                           [repo.full_name], {'lazy': False})
        if github_repo.fork:
            check_fork(github_repo, db.session, repo, repos_to_scan)

        # Check if repos should b
        if repo.should_scan():
            repos_to_scan.add(github_repo.full_name)

        repo_count += 1
        if repo_count % 100 == 0 or repo_count == len(repos):
            print(f'Get batch {repo_count}')
            db.session.commit()
            manager = Manager('github_repository', repos_to_scan)
            manager.start()
            manager.run()
            repos_to_scan = set()

    manager = Manager('github_repository', repos_to_scan)
    manager.start()
    manager.run()

    db.session.commit()
