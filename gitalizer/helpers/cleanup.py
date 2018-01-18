"""Clean stuff from db, which occured through bugs."""
import sys
from gitalizer.extensions import db
from gitalizer.models import Contributer, Repository, Commit


def clean_db():
    """Clean stuff."""
    print("Removing Linus stuff.")
    linus = db.session.query(Contributer).get('JamesLinus')
    for repository in linus.repositories:
        print(f'Deleting {repository.clone_url}')
        db.session.delete(repository)
    db.session.commit()

    print("Removing empty repos.")
    all_repositories = db.session.query(Repository).all()
    for repository in all_repositories:
        if not repository.fork and len(repository.commits) == 0:
            print(f'Deleting {repository.clone_url}')
            db.session.delete(repository)
    db.session.commit()

    print("Removing commits from fork repos.")
    all_repositories = db.session.query(Repository).all()
    for repository in all_repositories:
        if repository.fork and len(repository.commits) > 0:
            print(f'Removing commits from {repository.clone_url}')
            db.session.query(Commit) \
                .filter(Commit.repository == repository) \
                .delete()
    db.session.commit()
