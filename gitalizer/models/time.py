"""Module containing the `User` model."""
from gitalizer.extensions import db


class TimezoneInterval(db.Model):
    """This class represents lol."""

    __tablename__ = 'timezone_interval'
    __table_args__ = (
        db.CheckConstraint('"start" < "end"'),
    )

    timezone = db.Column(db.String(120), nullable=False, primary_key=True)
    utcoffset = db.Column(db.Interval(), index=True)
    start = db.Column(db.DateTime(timezone=True), index=True, primary_key=True)
    end = db.Column(db.DateTime(timezone=True), index=True, primary_key=True)

    def __init__(self, timezone, offset, start, end):
        """Create a new TimezoneInterval."""
        self.timezone = timezone
        self.utcoffset = offset
        self.end = end
        self.start = start

    def __repr__(self):
        """Format a `TimezoneInterval` object."""
        return f'<TimezoneInterval {self.timezone}, {self.utcoffset}, {self.start}-{self.end}>'
