"""Representation of a git repository."""

from gitalizer.extensions import db
from gitalizer.models.contributer import contributer_repositories


class Repository(db.Model):
    """Repository model."""

    __tablename__ = 'repository'
    clone_url = db.Column(db.String(240), primary_key=True)

    commits = db.relationship("Commit", back_populates="repository")
    contributors = db.relationship(
        "Contributer",
        secondary=contributer_repositories,
        back_populates="repositories")

    def __init__(self, clone_url):
        """Constructor."""
        self.clone_url = clone_url
