"""Clean stuff from db, which occured through bugs."""
from flask import current_app
from datetime import datetime, timedelta
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from gitalizer.extensions import db
from gitalizer.models import (
    Repository,
    Commit,
    Contributor,
    Email,
)
from gitalizer.helpers.parallel import new_session
from gitalizer.helpers.parallel.manager import Manager
from gitalizer.helpers.parallel.list_manager import ListManager


def clean_db():
    """Clean stuff."""
    current_app.logger.info("Removing commits from fork repos.")
    all_repositories = db.session.query(Repository) \
        .filter(Repository.fork.is_(True)) \
        .filter(Repository.commits != None) \
        .options(joinedload(Repository.commits)) \
        .all()

    current_app.logger.info(f'Found {len(all_repositories)}')
    repositories_count = 0
    for repository in all_repositories:
        repository.commits = []
        db.session.add(repository)
        repositories_count += 1
        if repositories_count % 100 == 0:
            current_app.logger.info(f'Removed {repositories_count}')
            db.session.commit()

    current_app.logger.info("Remove unattached commits")
    db.session.query(Commit) \
        .filter(Commit.repositories == None) \
        .delete()
    db.session.commit()


def complete_data():
    """Complete missing entities."""
    complete_contributor()
    complete_repos()


def complete_repos():
    """Complete unfinished repsitories."""
    current_app.logger.info("Get unfinished or out of date repositories.")
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
    current_app.logger.info(f'Found {len(repos)}')

    full_names = [r.full_name for r in repos]
    repos_to_scan = set(full_names)

    manager = Manager('github_repository', repos_to_scan)
    manager.start()
    manager.run()

    session.close()


def complete_contributor():
    """Complete contributor."""
    session = new_session()
    current_app.logger.info(f'Start Scan.')

    # Look at the last two years
    time_span = datetime.now() - timedelta(days=2*365)

    results = session.query(Contributor, func.array_agg(Commit.sha)) \
        .filter(Contributor.login == Contributor.login) \
        .join(Email, Contributor.login == Email.contributor_login) \
        .join(Commit, or_(
            Commit.author_email_address == Email.email,
            Commit.committer_email_address == Email.email,
        )) \
        .filter(Commit.commit_time >= time_span) \
        .filter(or_(
            Contributor.location == None,
        )) \
        .group_by(Contributor.login) \
        .all()

    current_app.logger.info(f'Scanning {len(results)} contributors.')

    count = 0
    big_contributors = []
    for contributor, commits in results:
        if len(commits) > 100 and len(commits) < 20000:
            big_contributors.append((contributor, commits))

        count += 1
        if count % 5000 == 0:
            current_app.logger.info(f'Scanned {count} contributors ({len(big_contributors)} big)')


    manager = ListManager('github_user', big_contributors)
    manager.start()
    manager.run()
