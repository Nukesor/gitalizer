"""Representation of a git repository contributor."""
from uuid import uuid4
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from gitalizer.extensions import db


class AnalysisResult(db.Model):
    """Analysis results."""

    __tablename__ = 'analysis_result'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contributer_login = db.Column(
        db.String(240),
        ForeignKey('contributor.login', ondelete='CASCADE',
                   onupdate='CASCADE', deferrable=True),
        index=True)

    # Timezone check
    different_timezones = db.Column(db.Integer())
    last_change = db.Column(db.DateTime())

    # Relationships
    contributor = db.relationship("Contributor", back_populates="analysis_result")
