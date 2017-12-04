"""Helper functions to manage sessions between processes."""

from sqlalchemy.orm import sessionmaker
from gitalizer.extensions import db  # noqa


def new_session():
    """Create a new session."""
    session = sessionmaker(bind=db.engine)()
    return session
