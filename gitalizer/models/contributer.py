"""Representation of a git repository contributer."""

from flask import current_app
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from gitalizer.extensions import db


contributer_repository = db.Table(
    'contributer_repository',
    db.Column('contributer_login',
              db.String(240),
              ForeignKey('contributer.login', ondelete='CASCADE', deferrable=True),
              index=True),
    db.Column('repository_clone_url',
              db.String(240),
              ForeignKey('repository.clone_url', ondelete='CASCADE', deferrable=True),
              index=True),
    db.UniqueConstraint('repository_clone_url', 'contributer_login'),
)


contributer_organizations = db.Table(
    'contributer_organizations',
    db.Column('contributer_login',
              db.String(240),
              ForeignKey('contributer.login', ondelete='CASCADE', deferrable=True),
              index=True),
    db.Column('organization_login',
              db.String(240),
              ForeignKey('organization.login', ondelete='CASCADE', deferrable=True),
              index=True),
    db.UniqueConstraint('contributer_login', 'organization_login'),
)


class Contributer(db.Model):
    """Contributer model."""

    __tablename__ = 'contributer'

    login = db.Column(db.String(240), primary_key=True, nullable=False)
    emails = db.relationship("Email", back_populates="contributer")
    repositories = db.relationship(
        "Repository",
        secondary=contributer_repository,
        back_populates="contributors")
    organizations = db.relationship(
        "Organization",
        secondary=contributer_organizations,
        back_populates="contributors")

    too_big = db.Column(db.Boolean, default=False, server_default='FALSE', nullable=False)
    last_full_scan = db.Column(db.DateTime(timezone=True))

    def __init__(self, login: str):
        """Constructor."""
        self.login = login

    def __repr__(self):
        """Format a `User` object."""
        return f'<User {self.login}>'

    @staticmethod
    def get_contributer(login: str, session, eager_repositories=False, do_commit=True):
        """Create new contributer or add repository to it's list.

        Try multiple times, as we can get Multiple additions through threading.
        """
        _try = 0
        tries = 3
        exception = None
        while _try <= tries:
            try:
                contributer = session.query(Contributer)
                if eager_repositories:
                    contributer.options(joinedload(Contributer.repositories))
                contributer = contributer.get(login)
                if not contributer:
                    # Commit to prevent data loss in case we get an
                    # integrity error and need to rollback.
                        contributer = Contributer(login)
                session.add(contributer)
                if do_commit:
                    session.commit()
                return contributer
            except IntegrityError as e:
                print(f'Got an Contributer IntegrityError, Try {_try} of {tries}')
                session.rollback()
                _try += 1
                exception = e
                pass

        raise exception

    def should_scan(self):
        """Check if the user has been scanned in the last day.

        If that is the case, we want to skip it.
        """
        no_repositories = len(self.repositories) == 0
        if no_repositories or self.last_full_scan is None:
            return True

        timeout = datetime.utcnow() - current_app.config['CONTRIBUTER_RESCAN_TIMEOUT']
        up_to_date = self.last_full_scan and self.last_full_scan >= timeout

        if not up_to_date:
            return True

        return False
