"""Analyse the efficiency of the travel path comparison."""
import os
import numpy as np
from pprint import pformat
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


def analyse_punch_card(existing=False):
    """Analyze the efficiency of the missing time comparison."""
    session = new_session()
    current_app.logger.info(f'Start Scan.')

    # If the only_existing parameter is given, we only work with
    # the existing intermediate AnalysisResults.
    if not existing:
        # Only look at commits of the last year
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

    if existing:
        current_app.logger.info(f'Analysing {len(analysis_results)} results.')

    vectorized_data = []
    for result in analysis_results:
        if 'punchcard' in result.intermediate_results:
            vectorized_data.append(result.intermediate_results['punchcard'])

    eps = 100
    min_samples = 10
    db = DBSCAN(eps=eps, min_samples=min_samples, metric='l1', n_jobs=-1).fit(vectorized_data)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    # Number of entities per label
    unique, counts = np.unique(labels, return_counts=True)
    occurrences = dict(zip(unique, counts))

    # Number of clusters in labels, ignoring noise if present.
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    silhouette = metrics.silhouette_score(vectorized_data, labels)

    # Prepare the plot dir for prototype plotting
    plot_dir = current_app.config['PLOT_DIR']
    plot_dir = os.path.join(plot_dir, 'analysis')
    plot_dir = os.path.join(plot_dir, 'analyse_punch')
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    # Get the mean-center prototypes for each label and plot them
    prototypes = get_core_sample_prototypes(db, vectorized_data)
    for label, prototype in prototypes.items():
        path = os.path.join(plot_dir, str(label))
        plotter = CommitPunchcard([], path, f'Prototype for {label}')
        plotter.preprocess()
        plotter.data['count'] = np.array(prototype) * 5
        plotter.plot()

    current_app.logger.info(f'DBSCAN with EPS: {eps} and {min_samples} min samples.')
    current_app.logger.info('Amount of entities in clusters. -1 is an outlier:')
    current_app.logger.info(pformat(occurrences))
    current_app.logger.info('Mean-core prototypes:')
    current_app.logger.info(pformat(prototypes))
    current_app.logger.info(f'Core samples: {len(db.core_sample_indices_)}')
    current_app.logger.info(f'{len(analysis_results)} contributers are relevant.')
    current_app.logger.info(f'Estimated number of clusters: {n_clusters}')
    current_app.logger.info("Silhouette Coefficient: {0:.3}".format(silhouette))

    return


def get_core_sample_prototypes(db, data):
    """Return the representative mean-center prototype of each cluster."""
    labels = db.labels_

    # Sort all core sample indices by their lable
    sample_indices_by_label = {}
    for index in db.core_sample_indices_:
        label = labels[index]

        # Create label list if it doesn't exist
        if label not in sample_indices_by_label:
            sample_indices_by_label[label] = []

        sample_indices_by_label[label].append(index)

    prototypes = {}
    for label, indices in sample_indices_by_label.items():
        runner = [0] * 168
        for index in indices:
            runner = np.add(runner, data[index])

        mean_center = np.divide(runner, len(indices))
        prototypes[label] = np.around(mean_center, 2).tolist()

    return prototypes


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
