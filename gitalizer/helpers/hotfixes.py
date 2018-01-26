"""Clean stuff from db, which occured through bugs."""
from flask import current_app
from datetime import datetime
from sqlalchemy import or_
from gitalizer.extensions import db
from gitalizer.models import Repository, Commit
from gitalizer.aggregator.parallel.manager import Manager


def clean_db():
    """Clean stuff."""
    print("Removing empty repos.")
    db.session.query(Repository) \
        .filter(Repository.commits == None) \
        .filter(Repository.fork.is_(False)) \
        .filter(Repository.broken.is_(False)) \
        .delete(synchronize_session='fetch')
    db.session.commit()

    print("Removing commits from fork repos.")
    all_repositories = db.session.query(Repository) \
        .filter(Repository.fork.is_(True)) \
        .filter(Repository.commits != None) \
        .all()
    print('Found f{len(all_repositories}')

    for repository in all_repositories:
        print(f'Removing commits from {repository.clone_url}')
        db.session.query(Commit) \
            .filter(Commit.repository == repository) \
            .delete()
    db.session.commit()


def complete_data():
    """Clean stuff."""
    print("Get non up to date.")
    timeout_threshold = datetime.utcnow() - current_app.config['REPOSITORY_RESCAN_TIMEOUT']

    repos = db.session.query(Repository) \
        .filter(Repository.fork.is_(False)) \
        .filter(Repository.broken.is_(False)) \
        .filter(or_(
            Repository.updated_at <= timeout_threshold,
            Repository.completely_scanned.is_(False),
        )) \
        .all()

    repos_to_scan = [r.full_name for r in repos]

    manager = Manager('github_repository', repos_to_scan)
    manager.start()
    manager.run()

    db.session.commit()
