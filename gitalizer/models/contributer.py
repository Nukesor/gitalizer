from flask import current_app
from gitalizer.extensions import db


class User(db.Model, Timestamp):
    """User model."""

    login = db.Column(String(120), primary_key=True, nullable=False)

    def __init__(self, login):
        self.login = login

    def __repr__(self):
        """Format a `User` object."""
        return f'<User {self.login}>'

