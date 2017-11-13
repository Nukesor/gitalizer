"""Helper for github crawling."""

from datetime import datetime, timedelta
from gitalizer.extensions import db
from gitalizer.models import Repository


def should_scan_repository(clone_url: str):
    """Check if the repo has been updated in the last hour.

    If that is the case, we want to skip it.
    """
    one_hour_ago = datetime.now() - timedelta(hours=24)
    repo = db.session.query(Repository) \
        .filter(Repository.clone_url == clone_url) \
        .filter(Repository.completely_scanned == True) \
        .filter(Repository.updated_at >= one_hour_ago) \
        .one_or_none()
    if repo:
        return False
    return True
