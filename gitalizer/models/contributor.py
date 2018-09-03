"""Representation of a git repository contributor."""

from datetime import datetime, timezone
from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from gitalizer.helpers import get_config
from gitalizer.extensions import db, logger


contributor_repository = db.Table(
    'contributor_repository',
    db.Column('contributor_login',
              db.String(240),
              ForeignKey('contributor.login', ondelete='CASCADE',
                         onupdate='CASCADE', deferrable=True),
              index=True),
    db.Column('repository_clone_url',
              db.String(240),
              ForeignKey('repository.clone_url', ondelete='CASCADE',
                         onupdate='CASCADE', deferrable=True),
              index=True),
    db.UniqueConstraint('repository_clone_url', 'contributor_login'),
)


contributor_organizations = db.Table(
    'contributor_organizations',
    db.Column('contributor_login',
              db.String(240),
              ForeignKey('contributor.login', ondelete='CASCADE',
                         onupdate='CASCADE', deferrable=True),
              index=True),
    db.Column('organization_login',
              db.String(240),
              ForeignKey('organization.login', ondelete='CASCADE',
                         onupdate='CASCADE', deferrable=True),
              index=True),
    db.UniqueConstraint('contributor_login', 'organization_login'),
)


class Contributor(db.Model):
    """Contributor model."""

    __tablename__ = 'contributor'

    login = db.Column(db.String(240), primary_key=True, nullable=False)
    emails = db.relationship("Email", back_populates="contributor")
    location = db.Column(db.String(240))

    # Relationships
    repositories = db.relationship(
        "Repository",
        secondary=contributor_repository,
        back_populates="contributors")
    organizations = db.relationship(
        "Organization",
        secondary=contributor_organizations,
        back_populates="contributors")
    analysis_result = db.relationship(
        "AnalysisResult",
        uselist=False,
        back_populates="contributor")

    too_big = db.Column(db.Boolean, default=False, server_default='FALSE', nullable=False)
    last_full_scan = db.Column(db.DateTime(timezone=True))

    def __init__(self, login: str):
        """Constructor."""
        self.login = login

    def __repr__(self):
        """Format a `Contributor` object."""
        return f'<Contributor {self.login}>'

    @staticmethod
    def get_contributor(login: str, session, eager_repositories=False, do_commit=True):
        """Create new contributor or add repository to it's list.

        Try multiple times, as we can get Multiple additions through threading.
        """
        _try = 0
        tries = 3
        exception = None
        while _try <= tries:
            try:
                contributor = session.query(Contributor)
                if eager_repositories:
                    contributor.options(joinedload(Contributor.repositories))
                contributor = contributor.get(login)
                if not contributor:
                    # Commit to prevent data loss in case we get an
                    # integrity error and need to rollback.
                        contributor = Contributor(login)
                session.add(contributor)
                if do_commit:
                    session.commit()
                return contributor
            except IntegrityError as e:
                logger.error(f'Got an Contributor IntegrityError, Try {_try} of {tries}')
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

        timeout = datetime.now(timezone.utc) - get_config().CONTRIBUTER_RESCAN_TIMEOUT
        up_to_date = self.last_full_scan and self.last_full_scan >= timeout

        if not up_to_date:
            return True

        return False
