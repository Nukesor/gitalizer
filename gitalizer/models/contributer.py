"""Representation of a git repository contributer."""

from sqlalchemy import ForeignKey
from gitalizer.extensions import db


contributer_repositories = db.Table(
    'contributer_repositories',
    db.Column('contributer_login', db.String(240), ForeignKey('contributer.login')),
    db.Column('repository_url', db.String(240), ForeignKey('repository.clone_url')),
    db.UniqueConstraint('repository_url', 'contributer_login'),
)


class Contributer(db.Model):
    """Contributer model."""

    __tablename__ = 'contributer'
    login = db.Column(db.String(240), primary_key=True, nullable=False)

    emails = db.relationship("Email", back_populates="contributer")
    repositories = db.relationship(
        "Repository",
        secondary=contributer_repositories,
        back_populates="contributors")

    def __init__(self, login):
        """Constructor."""
        self.login = login

    def __repr__(self):
        """Format a `User` object."""
        return f'<User {self.login}>'
