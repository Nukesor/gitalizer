"""Data collection from Github."""

import socket

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.repository import Repository
from gitalizer.models.contributer import Contributer


def get_contributer(login: str):
    """Create new contributer or add repository to it's list."""
    _try = 0
    tries = 3
    while _try <= tries:
        try:
            contributer = db.session.query(Contributer).get(login)
            if not contributer:
                contributer = Contributer(login)
            db.session.add(contributer)
            db.session.commit()
            return contributer
        except socket.timeout:
            print(f'Failed to receive contributers. Try {_try} of {tries}')
            pass
    raise Exception
