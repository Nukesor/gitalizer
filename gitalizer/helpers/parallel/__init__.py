"""Helper functions to manage sessions between processes."""

from sqlalchemy.orm import sessionmaker
from gitalizer.extensions import db


def new_session():
    """Create a new session."""
    session = sessionmaker(bind=db.engine)()
    return session


def create_chunks(l, n):
    """Chunk a list into n sized chunks."""
    n = max(1, n)
    return [l[i:i+n] for i in range(0, len(l), n)]
