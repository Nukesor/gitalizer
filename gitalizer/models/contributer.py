"""Representation of a git repository contributer."""

from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError
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
    organization_id = db.Column(UUID(as_uuid=True), ForeignKey('repository.clone_url'))

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

    @staticmethod
    def get_contributer(login: str):
        """Create new contributer or add repository to it's list.

        Try multiple times, as we can get Multiple additions through threading.
        """
        _try = 0
        tries = 3
        exception = None
        while _try <= tries:
            try:
                contributer = db.session.query(Contributer).get(login)
                if not contributer:
                    contributer = Contributer(login)
                db.session.add(contributer)
                db.session.commit()
                return contributer
            except IntegrityError as e:
                print(f'Got an Contributer IntegrityError, Try {_try} of {tries}')
                _try += 1
                exception = e
                pass

        raise exception
