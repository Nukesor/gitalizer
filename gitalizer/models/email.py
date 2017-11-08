"""Representation of a git author email."""

from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.exc import IntegrityError

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

    @staticmethod
    def get_email(email_address: str):
        """Create new email.

        Try multiple times, as we can get Multiple additions through threading.
        """
        _try = 0
        tries = 3
        exception = None
        while _try <= tries:
            try:
                email = db.session.query(Email).get(email_address)
                if not email:
                    email = Email(email_address)
                    db.session.add(email)
                    db.session.commit()
            except IntegrityError as e:
                print(f'Got an Email IntegrityError, Try {_try} of {tries}')
                _try += 1
                exception = e
                pass

        raise exception
