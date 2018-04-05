"""Analyse the efficiency of the travel path comparison."""
import numpy as np
from copy import deepcopy
from sklearn import metrics
from sklearn.cluster import DBSCAN

from flask import current_app
from sqlalchemy import or_, func
from datetime import timedelta, datetime

from gitalizer.helpers.parallel import new_session, create_chunks
from gitalizer.plot.plotting import CommitPunchcard
from gitalizer.helpers.parallel.list_manager import ListManager
from gitalizer.models import (
    AnalysisResult,
    Commit,
    Contributor,
    Email,
)


def analyse_punch_card():
    """Analyze the efficiency of the missing time comparison."""
    session = new_session()
    current_app.logger.info(f'Start Scan.')

    # Look at the last year
    time_span = datetime.now() - timedelta(days=365)

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
        if count % 50000 == 0:
            current_app.logger.info(f'Scanned {count} contributors ({len(big_contributors)} big)')

    # Finished searching for contributors with enough commits.
    current_app.logger.info(f'Analysing {len(big_contributors)} contributors.')

    # Chunk the contributor list into chunks of 100
    chunks = create_chunks(big_contributors, 100)

    manager = ListManager('analyse_punchcard', chunks)
    manager.start()
    manager.run()

    analysis_results = session.query(AnalysisResult) \
        .filter(AnalysisResult.intermediate_results != None) \
        .all()

    vectorized_data = []
    for result in analysis_results:
        if 'punchcard' in result.intermediate_results:
            vectorized_data.append(result.intermediate_results['punchcard'])

    db = DBSCAN(eps=10, min_samples=2).fit(vectorized_data)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    silhouette = metrics.silhouette_score(vectorized_data, labels)

    current_app.logger.info(f'Looked at {len(results)} contributors.')
    current_app.logger.info(f'{len(big_contributors)} are relevant.')
    current_app.logger.info(f'Estimated number of clusters: {n_clusters}')
    current_app.logger.info("Silhouette Coefficient: {0:.3}".format(silhouette))

    return


def get_punchcard_data(contributors_commits):
    """Analyse the travel path of a few contributers."""
    try:
        session = new_session()
        for contributor, commit_hashes in contributors_commits:
            # Query result again with current session.
            contributor = session.query(Contributor).get(contributor.login)
            result = contributor.analysis_result

            if result is None:
                result = AnalysisResult()
                contributor.analysis_result = result

            if result.intermediate_results is None:
                result.intermediate_results = {}

            commits_changed = (len(commit_hashes) != result.commit_count)
            if 'punchcard' not in result.intermediate_results or commits_changed:
                # Deepcopy intermediate result, otherwise the jsonb won't refresh.
                new_intermediate = deepcopy(result.intermediate_results)
                commits = session.query(Commit) \
                    .filter(Commit.sha.in_(commit_hashes)) \
                    .all()

                # Compute the final punchcard evaluation
                plotter = CommitPunchcard(commits, '/', '')
                plotter.preprocess()

                # Standartize data
                df = plotter.data
                mean = df['count'].mean()
                df['count'] = df['count']/mean

                # Add data to list
                vector = df['count'].values.tolist()

                # Save the standartized intermediate result into the database
                new_intermediate['punchcard'] = vector
                result.intermediate_results = new_intermediate
                result.last_change = datetime.now()
                result.commit_count = len(commits)

            session.add(result)
            session.add(contributor)
            session.commit()

    finally:
        session.close()

    return {'message': 'Success'}
