"""Analyse the efficiency of the travel path comparison."""
from pprint import pformat
from flask import current_app
from sqlalchemy import or_, func
from datetime import timedelta, datetime

from gitalizer.helpers.parallel import new_session, create_chunks
from gitalizer.plot.plotting import CommitPunchcard, CommitSimilarity
from gitalizer.helpers.parallel.list_manager import ListManager
from gitalizer.models import (
    Commit,
    Contributor,
    Email,
)


def analyse_punch_card():
    """Analyze the efficiency of the missing time comparison."""
    session = new_session()
    current_app.logger.info(f'Start Scan.')

    # Look at the last year
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

    manager = ListManager('analyse_punchcard', chunks)
    manager.start()
    manager.run()

    helper = CommitSimilarity(None, None, None, None, None)

    all_dfs = []
    for result in manager.results:
        all_dfs += result['results']

    buckets = []
    counter = 0
    while len(all_dfs) != 0:
        counter += 1
        if counter % 100 == 0:
            current_app.logger.info(f'Analysed {counter} contributors.')

        df = all_dfs.pop()
        for bucket in buckets:
            if helper.euclidean_distance(bucket['prototype'], df) < 5:
                bucket['count'] += 1
                continue

        buckets.append({'prototype': df, 'count': 1})

    for bucket in buckets:
        # Round to two decimal places for better readability
        prototype = bucket['prototype'].round(2)
        bucket['prototype'] = ', '.join(prototype['count'].astype(str))

    current_app.logger.info(pformat(buckets))
    current_app.logger.info(f'Looked at {len(results)} contributors.')
    current_app.logger.info(f'{len(big_contributors)} are relevant.')
    current_app.logger.info(f'Found {len(buckets)} buckets.')

    return


def get_punchcard_data(contributors_commits):
    """Analyse the travel path of a few contributers."""
    try:
        session = new_session()
        results = []
        for _, commit_hashes in contributors_commits:
            # Query result again with current session.

            commits = session.query(Commit) \
                .filter(Commit.sha.in_(commit_hashes)) \
                .all()

            plotter = CommitPunchcard(commits, '/', '')
            plotter.preprocess()
            results.append(plotter.data)

    finally:
        session.close()

    return {
        'message': 'Success',
        'results': results,
        }
