"""Sqlalchemy helper."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class DB(object):
    """Create an engine for easy session creation."""

    def __init__(self, config):
        """Lazy initializer which takes an `app` and sets up sentry."""
        self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        self.model = declarative_base(bind=self.engine)

    @property
    def session(self):
        """Short handle for getting a session.

        Also needed for backwards compatibility during refactoring.
        """
        return self.get_session()

    def get_session(self):
        """Create a new session."""
        session = sessionmaker(bind=self.engine)()
        return session()
