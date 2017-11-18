"""Representation of a git author email."""

import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError
from github import Repository as Github_Repository

from gitalizer.extensions import db, github
from gitalizer.models.contributer import Contributer
from gitalizer.aggregator.github import call_github_function


class Email(db.Model):
    """Email model."""

    __tablename__ = 'email'

    email = db.Column(db.String(240), primary_key=True)
    contributer_login = db.Column(db.String(240), ForeignKey('contributer.login'))

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
                return email
            except IntegrityError as e:
                print(f'Got an Email IntegrityError, Try {_try} of {tries}')
                _try += 1
                exception = e
                pass

        raise exception

    def get_github_relation(self, git_commit, github_repo: Github_Repository):
        """Get the related github contributer."""
        # No github repository or contributer already known. Early return.
        if not github_repo or self.contributer != None:
            return

        # If we know the github author of this commit
        # add it to this email address.
        github_commit = call_github_function(github_repo, 'get_commit', [git_commit.hex])
        if github_commit.author:
            contributer = Contributer.get_contributer(github_commit.author.login)
            self.contributer = contributer
        return
