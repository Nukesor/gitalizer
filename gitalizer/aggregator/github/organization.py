"""Data collection from Github."""

import pytz
from flask import current_app
from datetime import datetime, timedelta

from gitalizer.extensions import github
from gitalizer.models import Contributer, Organization
from gitalizer.aggregator.github import call_github_function
from gitalizer.aggregator.parallel import new_session


def get_github_organizations():
    """Refresh all user organizations."""
    # Get a new session to prevent spawning a db.session.
    # Otherwise we get problems as this session is used in each thread as well.
    session = new_session()

    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz)
    contributers = session.query(Contributer).all()
    for contributer in contributers:
        if contributer.last_check and contributer.last_check > now - timedelta(days=2):
            continue
        current_app.logger.info(f'Checking {contributer.login}. {github.github.rate_limiting[0]} remaining.')

        github_user = call_github_function(github.github, 'get_user',
                                           [contributer.login])

        github_orgs = call_github_function(github_user, 'get_orgs')
        for org in github_orgs:
            organization = Organization.get_organization(org.login, org.url, session)
            contributer.organizations.append(organization)
        contributer.last_check = datetime.utcnow()
        session.add(contributer)
        session.commit()
