"""Clean stuff from db, which occured through bugs."""
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
