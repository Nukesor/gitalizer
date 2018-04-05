"""Analyse the efficiency of the travel path comparison."""
from flask import current_app
from sqlalchemy import or_, func
from datetime import timedelta, datetime

from gitalizer.helpers.parallel import new_session, create_chunks
from gitalizer.plot.plotting import TravelPath
from gitalizer.helpers.parallel.list_manager import ListManager
from gitalizer.models import (
    AnalysisResult,
    Commit,
    Contributor,
    Email,
)


def analyse_travel_path():
    """Analyze the efficiency of the missing time comparison."""
    session = new_session()
    current_app.logger.info(f'Start Scan.')

    # Look at the last two years
    time_span = datetime.now() - timedelta(days=2*365)

    results = session.query(Contributor, func.array_agg(Commit.sha)) \
        .filter(Contributor.login == Contributor.login) \
        .join(Email, Contributor.login == Email.contributor_login) \
        .join(Commit, or_(
            Commit.author_email_address == Email.email,
            Commit.committer_email_address == Email.email,
        )) \
        .filter(Commit.commit_time >= time_span) \
        .group_by(Contributor.login) \
        .all()

    current_app.logger.info(f'Scanning {len(results)} contributors.')

    count = 0
    big_contributors = []
    for contributor, commits in results:
        if len(commits) > 100 and len(commits) < 20000:
            big_contributors.append((contributor, commits))

        count += 1
        if count % 5000 == 0:
            current_app.logger.info(f'Scanned {count} contributors ({len(big_contributors)} big)')

    # Finished searching for contributors with enough commits.
    current_app.logger.info(f'Analysing {len(big_contributors)} contributors.')

    # Chunk the contributor list into chunks of 100
    chunks = create_chunks(big_contributors, 100)

    manager = ListManager('analyse_travel_path', chunks)
    manager.start()
    manager.run()

    results = session.query(AnalysisResult).all()

    changed = 0
    unchanged = 0
    for result in results:
        if result.different_timezones > 1:
            changed += 1
        else:
            unchanged += 1

    current_app.logger.info(f'Looked at {len(results)} contributors.')
    current_app.logger.info(f'{len(big_contributors)} are relevant.')
    current_app.logger.info(f'Detected a change in {changed} of those.')
    current_app.logger.info(f'Detected no change in {unchanged} of those.')

    return


def analyse_contributer_travel_path(contributors_commits):
    """Analyse the travel path of a few contributers."""
    try:
        session = new_session()
        count = 0
        for contributor, commit_hashes in contributors_commits:
            # Query result again with current session.
            contributor = session.query(Contributor).get(contributor.login)
            result = contributor.analysis_result

            if result is None:
                result = AnalysisResult()
                contributor.analysis_result = result
                session.add(contributor)

            commits_changed = (len(commit_hashes) != result.commit_count)
            if result.different_timezones is None or commits_changed:
                commits = session.query(Commit) \
                    .filter(Commit.sha.in_(commit_hashes)) \
                    .all()

                plotter = TravelPath(commits, '/')
                plotter.preprocess()

                result.different_timezones = len(plotter.data)
                result.last_change = datetime.now()
                result.commit_count = len(commits)
                session.add(result)

            count += 1
            if count % 50 == 0:
                session.commit()

        session.commit()
    finally:
        session.close()

    return {'message': 'Success'}
