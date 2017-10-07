"""Representation of a git commit."""

import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint

from gitalizer.extensions import db


class Commit(db.Model):
    """Commit model."""

    __tablename__ = 'commit'
    __table_args__ = (
        ForeignKeyConstraint(['repository_url'], ['repository.clone_url']),
        ForeignKeyConstraint(['author_email'], ['email.email']),
        UniqueConstraint('sha', 'repository_url'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha = db.Column(db.String(40), nullable=False)
    time = db.Column(db.DateTime())
    author_email = db.Column(db.String(240), nullable=False)
    additions = db.Column(db.Integer())
    deletions = db.Column(db.Integer())
    repository_url = db.Column(db.String(240), nullable=False)

    repository = db.relationship("Repository", back_populates="commits")
    email = db.relationship("Email", back_populates="commits")

    def __init__(self, sha, repository, contributer):
        """Constructor."""
        self.sha = sha
        self.contributer = contributer
        self.repository = repository
