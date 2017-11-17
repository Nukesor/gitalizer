"""Module containing the `Organization` model."""
import uuid
import hmac
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils.models import Timestamp

from flask import current_app

from gitalizer.extensions import db, passlib


class Organization(db.Model, Timestamp):
    """Organization model."""

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    emails = db.relationship("Contributer", back_populates="organization")

    def __init__(self, name):
        """Construct an `Organization`."""
        self.name = name
