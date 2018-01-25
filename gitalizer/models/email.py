"""Representation of a git author email."""

from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError
from github.GithubObject import NotSet
from github import Repository as Github_Repository

from gitalizer.extensions import db, sentry
from gitalizer.models.contributer import Contributer
from gitalizer.aggregator.github import call_github_function


class Email(db.Model):
    """Email model."""

    __tablename__ = 'email'

    email = db.Column(db.String(240), primary_key=True)

    # Contributer
    contributer_login = db.Column(
        db.String(240), ForeignKey('contributer.login'), index=True,
    )
    contributer = db.relationship("Contributer", back_populates="emails")

    # Commits relationships
    author_commits = db.relationship(
        "Commit", back_populates="author_email",
        foreign_keys='Commit.author_email_address',
    )
    committer_commits = db.relationship(
        "Commit", back_populates="committer_email",
        foreign_keys='Commit.committer_email_address',
    )

    def __init__(self, email, contributer=None):
        """Constructor."""
        self.email = email
        self.contributer = contributer

    @staticmethod
    def get_email(email_address: str, session):
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
                    session.commit()
                return email
            except IntegrityError as e:
                print(f'Got an Email IntegrityError, Try {_try} of {tries}')
                session.rollback()
                _try += 1
                exception = e
                pass

        raise exception

    def get_github_relation(self, git_commit, user_type, session,
                            github_repo: Github_Repository):
        """Get the related github contributer."""
        # Early return, as we have no github repository or
        # the contributer is already known.
        if not github_repo or self.contributer is not None:
            return

        # If we know the github author of this commit
        # add it to this email address.
        github_commit = call_github_function(github_repo, 'get_commit', [git_commit.hex])

        if user_type == 'author' and github_commit.author \
                and github_commit.author is not NotSet:
            # Workaround for issue https://github.com/PyGithub/PyGithub/issues/279
            if github_commit.author._url.value is None:
                sentry.sentry.captureMessage(
                    'Author has no _url',
                    level='info',
                    extra={
                        'clone_url': github_repo.clone_url,
                        'commit_hex': git_commit.hex,
                    },
                )
                return

            contributer = Contributer.get_contributer(
                github_commit.author.login,
                session,
            )
            self.contributer = contributer

        elif user_type == 'committer' and github_commit.committer \
                and github_commit.committer is not NotSet:
            # Workaround for issue https://github.com/PyGithub/PyGithub/issues/279
            if github_commit.committer._url.value is None:
                sentry.sentry.captureMessage(
                    'Committer has no _url',
                    level='info',
                    extra={
                        'clone_url': github_repo.clone_url,
                        'commit_hex': git_commit.hex,
                    },
                )
                return

            contributer = Contributer.get_contributer(
                github_commit.committer.login,
                session,
            )
            self.contributer = contributer
        return
