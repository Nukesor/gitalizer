"""User scan."""
import click

from gitalizer.extensions import db
from gitalizer.models import (
    Commit,
    commit_repository,
    Repository,
)


@click.group()
def delete():
    """Cli wrapper for the database delete command group."""
    pass


@click.command()
@click.argument('full_name')
def repository(full_name):
    """Delete a specific repository."""
    session = db.new_session()
    try:
        repository = session.query(Repository) \
            .filter(Repository.full_name == full_name) \
            .one()

        commit_shas = session.query(Commit.sha) \
            .join(
                commit_repository,
                commit_repository.c.repository_clone_url == repository.clone_url,
            ) \
            .filter(commit_repository.c.commit_sha == Commit.sha) \
            .all()

        commit_shas = [c[0] for c in commit_shas]
        if commit_shas:
            session.query(Commit) \
                .filter(Commit.sha.in_(commit_shas)) \
                .delete(synchronize_session=False)

        session.query(Repository) \
            .filter(Repository.full_name == full_name) \
            .delete()
        session.commit()
    finally:
        session.close()


delete.add_command(repository)
