from flask import current_app
from gitalizer.extensions import db


class Repository(db.Model, Timestamp):
    """User model."""

    clone_url = db.Column(String(240), primary_key=True)

    def __init__(self, clone_url):
        self.clone_url = clone_url
