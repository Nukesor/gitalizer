"""Representation of a git repository."""

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
    completely_scanned = db.Column(db.Boolean(), default=False)

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
