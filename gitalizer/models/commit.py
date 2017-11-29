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
            "(additions is not NULL and deletions is not NULL)",
        ),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha = db.Column(db.String(40), nullable=False)
    time = db.Column(db.DateTime(timezone=True))
    additions = db.Column(db.Integer())
    deletions = db.Column(db.Integer())

    # Email addresses
    author_email_address = db.Column(
        db.String(240), ForeignKey('email.email'),
        index=True, nullable=False,
    )
    committer_email_address = db.Column(
        db.String(240), ForeignKey('email.email'),
        index=True, nullable=False,
    )
    author_email = db.relationship(
        "Email", back_populates="author_commits",
        foreign_keys=[author_email_address],
    )
    committer_email = db.relationship(
        "Email", back_populates="committer_commits",
        foreign_keys=[committer_email_address],
    )

    # Repository
    repository_url = db.Column(db.String(240), ForeignKey('repository.clone_url'),
                               index=True, nullable=False)
    repository = db.relationship("Repository", back_populates="commits")

    def __init__(self, sha, repository, author_email, committer_email):
        """Constructor."""
        self.sha = sha
        self.author_email = author_email
        self.committer_email = committer_email
        self.repository = repository
