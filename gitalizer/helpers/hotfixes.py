"""Clean stuff from db, which occured through bugs."""
from sqlalchemy import func
from gitalizer.extensions import db
from gitalizer.models import Repository, Commit


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
    print("Get repos with missing full_name.")
    repos = db.session.query(Repository) \
        .filter(Repository.full_name.is_(None)) \
        .all()

    for repo in repos:
        name_parts = repo.clone_url.rsplit('/', 2)
        owner = name_parts[1]
        name = name_parts[2].rsplit('.', 1)[0]
        full_name = f'{owner}/{name}'
        repo.name = name
        repo.full_name = full_name
        db.session.add(repo)

    db.session.commit()


def migrate():
    """Migrate data in case of drastic db changes."""
    commits = db.session.query(Commit.sha, func.count(Commit.sha)) \
        .group_by(Commit.sha) \
        .limit(100000) \
        .all()

    import pprint
    pprint.pprint(commits)
