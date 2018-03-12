"""Module containing the `Organization` model."""
from sqlalchemy.exc import IntegrityError

from gitalizer.extensions import db
from gitalizer.models.contributor import contributor_organizations


class Organization(db.Model):
    """Organization model."""

    __tablename__ = 'organization'

    login = db.Column(db.String(240), primary_key=True)
    url = db.Column(db.String(240))

    contributors = db.relationship(
        "Contributor",
        secondary=contributor_organizations,
        back_populates="organizations")

    def __init__(self, login, url):
        """Construct an `Organization`."""
        self.login = login
        self.url = url

    @staticmethod
    def get_organization(login: str, url: str, session):
        """Create new organization or add repository to it's list.

        Try multiple times, as we can get Multiple additions through threading.
        """
        _try = 0
        tries = 3
        exception = None
        while _try <= tries:
            try:
                organization = session.query(Organization).get(login)
                if not organization:
                    organization = Organization(login, url)
                session.add(organization)
                session.commit()
                return organization
            except IntegrityError as e:
                print(f'Got an Organization IntegrityError, Try {_try} of {tries}')
                _try += 1
                exception = e
                pass

        raise exception
