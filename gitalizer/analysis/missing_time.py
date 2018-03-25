"""Analyse the efficiency of the travel path comparison."""
from flask import current_app
from sqlalchemy import or_, func
from datetime import timedelta, datetime

from gitalizer.extensions import db
from gitalizer.plot.helper.db import get_user_commits
from gitalizer.plot.plotting import TravelPath
from gitalizer.models import (
    Commit,
    Contributor,
    Email,
)


def analyse_travel_path():
    """Analyze the efficiency of the missing time comparison."""
    contributors = db.session.query(Contributor).all()
    current_app.logger.info(f'Scanning {len(contributors)} contributors.')

    # Look at the last two years
    time_span = datetime.now() - timedelta(days=2*365)

    count = 0
    big_contributors = []
    for contributor in contributors:
        commits = db.session.query(Commit.sha) \
            .filter(Commit.commit_time >= time_span) \
            .join(Email, or_(
                Email.email == Commit.author_email_address,
                Email.email == Commit.committer_email_address,
            )) \
            .join(Contributor, Email.contributor_login == contributor.login) \
            .filter(Contributor.login == contributor.login) \
            .all()

        if len(commits) > 200:
            big_contributors.append((contributor, commits))

        count += 1
        if count % 100 == 0:
            current_app.logger.info(f'Scanned {count} contributors ({len(big_contributors)} big)')

    found_change = 0
    for contributor, commits in big_contributors:
        plotter = TravelPath(contributor, commits)
        plotter.preprocess()

        if len(plotter.data) > 1:
            found_change += 1

    current_app.logger.info(f'Looked at {len(contributors)} contributors.')
    current_app.logger.info(f'{len(big_contributors)} are relevant.')
    current_app.logger.info(f'Detected a change in {found_change} of those.')

    return
