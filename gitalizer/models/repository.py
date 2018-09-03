"""Representation of a git repository."""

from datetime import datetime
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection

from gitalizer.helpers import get_config
from gitalizer.extensions import db
from gitalizer.models.commit import commit_repository
from gitalizer.models.contributor import contributor_repository


class Repository(db.Model):
    """Repository model."""

    __tablename__ = 'repository'

    clone_url = db.Column(db.String(240), primary_key=True)
    parent_url = db.Column(
        db.String(240),
        ForeignKey('repository.clone_url', ondelete='SET NULL',
                   onupdate='CASCADE', deferrable=True),
        index=True,
    )
    name = db.Column(db.String(240))
    full_name = db.Column(db.String(240), unique=True)
    created_at = db.Column(db.DateTime(timezone=True))

    fork = db.Column(db.Boolean(), default=False,
                     server_default='FALSE', nullable=False)
    broken = db.Column(db.Boolean(), default=False,
                       server_default='FALSE', nullable=False)
    too_big = db.Column(db.Boolean(), default=False,
                        server_default='FALSE', nullable=False)
    completely_scanned = db.Column(db.Boolean(), default=False,
                                   server_default='FALSE', nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    children = db.relationship(
        "Repository",
        backref=backref('parent', remote_side=[clone_url]),
    )

    commits = db.relationship(
        "Commit",
        secondary=commit_repository,
        back_populates="repositories",
    )
    commits_by_hash = db.relationship(
        "Commit",
        collection_class=attribute_mapped_collection('sha'),
        secondary=commit_repository,
    )

    contributors = db.relationship(
        "Contributor",
        secondary=contributor_repository,
        back_populates="repositories",
    )

    def __init__(self, clone_url, name=None, full_name=None):
        """Constructor."""
        self.clone_url = clone_url
        self.name = name
        self.full_name = full_name

    @staticmethod
    def get_or_create(session, clone_url: str, name=None, full_name=None):
        """Get an existing repository from db or create a new one."""
        repo = session.query(Repository).get(clone_url)

        if not repo:
            repo = Repository(clone_url, name, full_name)
            session.add(repo)
            session.commit()

        return repo

    def should_scan(self):
        """Check if the repo has been updated in the last day.

        If that is the case, we want to skip it.
        """
        timeout_threshold = datetime.utcnow() - get_config().REPOSITORY_RESCAN_TIMEOUT
        up_to_date = self.completely_scanned and self.updated_at >= timeout_threshold

        if self.fork or self.broken or self.too_big or up_to_date:
            return False

        return True

    def is_invalid(self):
        """Check if we should skip this repository for for checking."""
        return (self.broken or self.too_big)
