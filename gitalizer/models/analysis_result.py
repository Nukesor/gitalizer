"""Representation of analysis results."""
from uuid import uuid4
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

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
    commit_count = db.Column(db.Integer())
    timezone_switches = db.Column(db.Integer())
    different_timezones = db.Column(db.Integer())
    last_change = db.Column(db.DateTime())
    intermediate_results = db.Column(JSONB)

    # Relationships
    contributor = db.relationship("Contributor", back_populates="analysis_result")
