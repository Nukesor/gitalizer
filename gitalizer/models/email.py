"""Representation of a git author email."""

from sqlalchemy import ForeignKeyConstraint
from gitalizer.extensions import db


class Email(db.Model):
    """Email model."""

    __tablename__ = 'email'
    __table_args__ = (
        ForeignKeyConstraint(['contributer_login'], ['contributer.login']),
    )

    email = db.Column(db.String(240), primary_key=True)
    contributer_login = db.Column(db.String(240))

    contributer = db.relationship("Contributer", back_populates="emails")
    commits = db.relationship("Commit", back_populates="email")

    def __init__(self, email, contributer=None):
        """Constructor."""
        self.email = email
        self.contributer = contributer
