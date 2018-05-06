"""Analyse the efficiency of the travel path comparison."""
from copy import deepcopy
from pprint import pformat
from flask import current_app
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload
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


def analyse_travel_path(existing):
    """Analyze the efficiency of the missing time comparison."""
    session = new_session()
    current_app.logger.info(f'Start Scan.')

    # Look at the last two years
    time_span = datetime.now() - timedelta(days=2*365)

    if not existing:
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

    # Only look at commits of the last year
    results = session.query(AnalysisResult) \
        .filter(AnalysisResult.different_timezones != None) \
        .filter(and_(
            AnalysisResult.commit_count != None,
            AnalysisResult.commit_count > 100,
            AnalysisResult.commit_count < 20000,
        )) \
        .options(joinedload('contributor')) \
        .all()

    changed = 0
    unchanged = 0
    distribution = {}
    for result in results:
        amount = result.different_timezones
        if amount > 1:
            changed += 1
        else:
            unchanged += 1

        if distribution.get(amount) is None:
            distribution[amount] = 1
        else:
            distribution[amount] += 1

    correct = 0
    considered_contributors = 0
    for result in results:
        contributor = result.contributor
        home = result.intermediate_results['home']['set']

        if contributor.location is None:
            continue

        if element_in_string(contributor.location, [
                'Germany', 'Deutschland', 'France',
                'Italy', 'Spain', 'Poland', 'Austria',
        ]):
            considered_contributors += 1
            if 'Europe/Berlin' in home:
                correct += 1

        elif element_in_string(contributor.location, ['New Zealand']):
            considered_contributors += 1
            if 'Pacific/Auckland' in home:
                correct += 1

        elif element_in_string(contributor.location, ['UK', 'United Kingdom']):
            considered_contributors += 1
            if 'Europe/London' in home:
                correct += 1

        elif element_in_string(contributor.location, ['NY', 'New York']):
            considered_contributors += 1
            if 'America/New_York' in home:
                correct += 1

        elif element_in_string(contributor.location, ['Los Angeles']):
            considered_contributors += 1
            if 'America/Los_Angeles' in home:
                correct += 1

        elif element_in_string(contributor.location, ['Seattle', 'portland']):
            considered_contributors += 1
            if 'US/Pacific' in home:
                correct += 1

        elif element_in_string(contributor.location, ['Japan', '日本']):
            considered_contributors += 1
            if 'Japan' in home:
                correct += 1

        elif element_in_string(contributor.location, ['India']):
            considered_contributors += 1
            if 'Indian/Cocos' in home:
                correct += 1


    current_app.logger.info(f'Looked at {len(results)} contributors.')
    current_app.logger.info(f'{len(results)} are relevant.')
    current_app.logger.info(f'Detected a change in {changed} of those.')
    current_app.logger.info(f'Detected no change in {unchanged} of those.')
    current_app.logger.info(f'Distribution of users by amount of different timezones:')
    current_app.logger.info(pformat(distribution))
    current_app.logger.info(f'Verified contributors {correct} of {considered_contributors}')

    return


def element_in_string(string, word_list):
    for word in word_list:
        if word in string:
            return True

    return False


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
                session.add(result)

            commits_changed = (len(commit_hashes) != result.commit_count)

            # Look at the jsonb intermediate_result to see if we already wrote the data into it
            json_results = result.intermediate_results
            if json_results is None:
                json_results = {}
                result.intermediate_results = json_results

            if result.different_timezones is None \
                    or commits_changed \
                    or json_results.get('travel') is None \
                    or json_results.get('home') is None:
                commits = session.query(Commit) \
                    .filter(Commit.sha.in_(commit_hashes)) \
                    .all()

                plotter = TravelPath(commits, '/')
                plotter.preprocess()

                json_results = deepcopy(result.intermediate_results)

                for timezone_set in plotter.data:
                    del(timezone_set['start'])
                    del(timezone_set['end'])
                    timezone_set['set'] = list(timezone_set['set'])

                json_results['home'] = plotter.home_zone
                json_results['travel'] = plotter.data
                result.intermediate_results = json_results

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
