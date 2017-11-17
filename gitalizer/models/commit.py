"""Representation of a git commit."""

import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint

from gitalizer.extensions import db


class Commit(db.Model):
    """Commit model."""

    __tablename__ = 'commit'
    __table_args__ = (
        UniqueConstraint('sha', 'repository_url'),
        CheckConstraint(
            "(additions is NULL and deletions is NULL) or "
            "(additions is not NULL and deletions is not NULL)"
        ),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha = db.Column(db.String(40), nullable=False)
    time = db.Column(db.DateTime(timezone=True))
    author_email = db.Column(db.String(240), nullable=False, ForeignKey('email.email'))
    additions = db.Column(db.Integer())
    deletions = db.Column(db.Integer())
    repository_url = db.Column(db.String(240), nullable=False, ForeignKey('repository.clone_url'))

    email = db.relationship("Email", back_populates="commits")
    repository = db.relationship("Repository", back_populates="commits")

    def __init__(self, sha, repository, email):
        """Constructor."""
        self.sha = sha
        self.email = email
        self.repository = repository
