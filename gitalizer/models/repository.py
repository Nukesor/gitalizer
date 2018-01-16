"""Representation of a git repository."""

from datetime import datetime
from flask import current_app
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import backref

from gitalizer.extensions import db
from gitalizer.models.contributer import contributer_repositories


class Repository(db.Model):
    """Repository model."""

    __tablename__ = 'repository'

    clone_url = db.Column(db.String(240), primary_key=True)
    parent_url = db.Column(db.String(240), ForeignKey('repository.clone_url'), index=True)
    name = db.Column(db.String(240))
    created_at = db.Column(db.DateTime(timezone=True))

    completely_scanned = db.Column(db.Boolean(), default=False, nullable=False)
    broken = db.Column(db.Boolean(), default=False, nullable=False)

    children = db.relationship("Repository", backref=backref('parent', remote_side=[clone_url]))
    commits = db.relationship("Commit", back_populates="repository")
    contributors = db.relationship(
        "Contributer",
        secondary=contributer_repositories,
        back_populates="repositories")
    updated_at = db.Column(
        db.DateTime, server_default=func.now(),
        nullable=False,
    )

    def __init__(self, clone_url, name=None):
        """Constructor."""
        self.clone_url = clone_url
        self.name = name

    @staticmethod
    def get_or_create(session, clone_url: str, name=None):
        repo = session.query(Repository).get(clone_url)

        if not repo:
            repo = Repository(clone_url, name)
            session.add(repo)
            session.commit()

        return repo

    def should_scan(self):
        """Check if the repo has been updated in the last day.

        If that is the case, we want to skip it.
        """
        timeout_threshold = datetime.utcnow() - current_app.config['REPOSITORY_RESCAN_TIMEOUT']
        if self.completely_scanned and self.updated_at >= timeout_threshold:
            return False

        return True
