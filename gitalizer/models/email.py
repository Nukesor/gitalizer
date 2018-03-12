"""Representation of a git author email."""

from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError

from gitalizer.extensions import db


class Email(db.Model):
    """Email model."""

    __tablename__ = 'email'

    email = db.Column(db.String(240), primary_key=True)

    # Contributor
    contributor_login = db.Column(
        db.String(240), ForeignKey('contributor.login'), index=True,
    )
    contributor = db.relationship("Contributor", back_populates="emails")

    # Commits relationships
    author_commits = db.relationship(
        "Commit", back_populates="author_email",
        foreign_keys='Commit.author_email_address',
    )
    committer_commits = db.relationship(
        "Commit", back_populates="committer_email",
        foreign_keys='Commit.committer_email_address',
    )
    unknown = db.Column(db.Boolean(), default=False)

    def __init__(self, email, contributor=None):
        """Constructor."""
        self.email = email
        self.contributor = contributor

    @staticmethod
    def get_email(email_address: str, session, do_commit=True):
        """Create new email.

        Try multiple times, as we can get Multiple additions through threading.
        """
        _try = 0
        tries = 3
        exception = None
        while _try <= tries:
            try:
                email = session.query(Email).get(email_address)
                if not email:
                    email = Email(email_address)
                    session.add(email)
                    if do_commit:
                        session.commit()
                return email
            except IntegrityError as e:
                print(f'Got an Email IntegrityError, Try {_try} of {tries}')
                session.rollback()
                _try += 1
                exception = e
                pass

        raise exception
