"""Representation of a git repository contributer."""

from flask import current_app
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError

from gitalizer.extensions import db


contributer_repositories = db.Table(
    'contributer_repositories',
    db.Column('contributer_login', db.String(240), ForeignKey('contributer.login'), index=True),
    db.Column('repository_url', db.String(240), ForeignKey('repository.clone_url'), index=True),
    db.UniqueConstraint('repository_url', 'contributer_login'),
)


contributer_organizations = db.Table(
    'contributer_organizations',
    db.Column('contributer_login', db.String(240),
              ForeignKey('contributer.login')),
    db.Column('organization_login', db.String(240),
              ForeignKey('organization.login')),
    db.UniqueConstraint('contributer_login', 'organization_login'),
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
    organizations = db.relationship(
        "Organization",
        secondary=contributer_organizations,
        back_populates="contributors")

    too_big = db.Column(db.Boolean, default=False, nullable=False)
    last_check = db.Column(db.DateTime(timezone=True))
    full_scan = db.Column(db.DateTime(timezone=True))

    def __init__(self, login: str):
        """Constructor."""
        self.login = login

    def __repr__(self):
        """Format a `User` object."""
        return f'<User {self.login}>'

    @staticmethod
    def get_contributer(login: str, session):
        """Create new contributer or add repository to it's list.

        Try multiple times, as we can get Multiple additions through threading.
        """
        _try = 0
        tries = 3
        exception = None
        while _try <= tries:
            try:
                contributer = session.query(Contributer).get(login)
                if not contributer:
                    # Commit to prevent data loss in case we get an
                    # integrity error and need to rollback.
                    session.commit()
                    contributer = Contributer(login)
                session.add(contributer)
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
        timeout = datetime.utcnow() - current_app.config['CONTRIBUTER_RESCAN_TIMEOUT']
        if len(self.repositories) == 0:
            return True

        for repository in self.repositories:
            if repository.fork:
                continue

            if repository.completely_scanned and repository.updated_at <= timeout:
                continue

            return True

        return False
