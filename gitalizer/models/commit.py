"""Representation of a git commit."""
from sqlalchemy import ForeignKey, CheckConstraint

from gitalizer.extensions import db


commit_repository = db.Table(
    'commit_repository',
    db.Column('commit_sha',
              db.String(40),
              ForeignKey('commit.sha', ondelete='CASCADE',
                         onupdate='CASCADE', deferrable=True),
              index=True),
    db.Column('repository_clone_url',
              db.String(240),
              ForeignKey('repository.clone_url', ondelete='CASCADE',
                         onupdate='CASCADE', deferrable=True),
              index=True),
    db.UniqueConstraint('repository_clone_url', 'commit_sha'),
)


class Commit(db.Model):
    """Commit model."""

    __tablename__ = 'commit'
    __table_args__ = (
        CheckConstraint(
            "(additions is NULL and deletions is NULL) or "
            "(additions is not NULL and deletions is not NULL)",
        ),
    )

    sha = db.Column(db.String(40), primary_key=True)
    commit_time = db.Column(db.DateTime(timezone=True))
    commit_time_offset = db.Column(db.Interval())
    creation_time = db.Column(db.DateTime(timezone=True))
    creation_time_offset = db.Column(db.Interval())
    additions = db.Column(db.Integer())
    deletions = db.Column(db.Integer())

    # Email addresses
    author_email_address = db.Column(
        db.String(240), ForeignKey('email.email'),
        index=True, nullable=False,
    )
    committer_email_address = db.Column(
        db.String(240), ForeignKey('email.email'),
        index=True, nullable=False,
    )
    author_email = db.relationship(
        "Email", back_populates="author_commits",
        foreign_keys=[author_email_address],
    )
    committer_email = db.relationship(
        "Email", back_populates="committer_commits",
        foreign_keys=[committer_email_address],
    )

    repositories = db.relationship(
        "Repository",
        secondary=commit_repository,
        back_populates="commits",
    )

    def __init__(self, sha, repository, author_email, committer_email):
        """Constructor."""
        self.sha = sha
        self.author_email = author_email
        self.committer_email = committer_email
        self.repositories.append(repository)

    def local_time(self):
        """Get the local commit time for this commit."""
        new_time = self.commit_time
        if self.commit_time.utcoffset():
            new_time = self.commit_time - self.commit_time.utcoffset()
            new_time = new_time.replace(tzinfo=None)
            new_time += self.commit_time_offset

        return new_time
