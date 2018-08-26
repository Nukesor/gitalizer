"""Analyse the efficiency of the travel path comparison."""
from copy import deepcopy
from pprint import pformat
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload
from datetime import timedelta, datetime

from gitalizer.extensions import logger
from gitalizer.helpers.parallel import new_session, create_chunks
from gitalizer.plot.plotting import TravelPath
from gitalizer.helpers.parallel.list_manager import ListManager
from gitalizer.models import (
    AnalysisResult,
    Commit,
    Contributor,
    Email,
)

timezone_evaluations = [
    {"search": ['Germany', 'Deutschland'], "timezone": 'Europe/Berlin'},
    {"search": ['France'], "timezone": 'Europe/Paris'},
    {"search": ['Italy'], "timezone": 'Europe/Rome'},
    {"search": ['Spain'], "timezone": 'Europe/Madrid'},
    {"search": ['Poland'], "timezone": 'Europe/Warsaw'},
    {"search": ['UK', 'United Kingdom'], "timezone": 'Europe/London'},
    {"search": ['New Zealand'], "timezone": 'Pacific/Auckland'},
    {"search": ['NYC', 'NY', 'New York'], "timezone": 'America/New_York'},
    {"search": ['Los Angeles'], "timezone": 'America/Los_Angeles'},
    {"search": ['Tokyo'], "timezone": 'Pacific/Palau'},
    {"search": ['India'], "timezone": 'Asia/Colombo'},
    {"search": ['Sidney'], "timezone": 'Australia/NSW'},
    {"search": ['Adelaide'], "timezone": 'Australia/Adelaide'},
    {"search": ['Jamaica'], "timezone": 'America/Jamaica'},
    {"search": ['Mexico'], "timezone": 'Mexico/General'},
    {"search": ['San Francisco'], "timezone": 'US/Pacific'},
]


def analyse_travel_path(existing):
    """Analyze the efficiency of the missing time comparison."""
    session = new_session()
    logger.info(f'Start Scan.')

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

        logger.info(f'Scanning {len(results)} contributors.')

        count = 0
        big_contributors = []
        for contributor, commits in results:
            if len(commits) > 100 and len(commits) < 20000:
                big_contributors.append((contributor, commits))

            count += 1
            if count % 5000 == 0:
                logger.info(f'Scanned {count} contributors ({len(big_contributors)} big)')

        # Finished searching for contributors with enough commits.
        logger.info(f'Analysing {len(big_contributors)} contributors.')

        # Chunk the contributor list into chunks of 100
        chunks = create_chunks(big_contributors, 100)

        manager = ListManager('analyse_travel_path', chunks)
        manager.start()
        manager.run()

    # Only look at commits of the last year
    results = session.query(AnalysisResult) \
        .filter(AnalysisResult.timezone_switches != None) \
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
        amount = result.timezone_switches
        if amount > 1:
            changed += 1
        else:
            unchanged += 1

        if distribution.get(amount) is None:
            distribution[amount] = 1
        else:
            distribution[amount] += 1

    ignored_timezones = set([
        'GB', 'WET', 'MET', 'CET', 'EET',
        'NZ', 'MST7MDT', 'PST8PDT', 'CST6CDT', 'W-SU',
        'ROK', 'EET', 'NZ-CHAT', 'GB-Eire', 'ROC',
        'EST5EDT', 'EET', 'PRC',
    ])
    for i in range(0, 16):
        ignored_timezones.add(f'GMT-{i}')
        ignored_timezones.add(f'GMT+{i}')

    correct = 0
    considered_contributors = 0
    survey_results = {}
    detected_timezones = {}
    for result in results:
        contributor = result.contributor
        home = set(result.intermediate_results['home']['set'])
        if 'full_set' in result.intermediate_results['home']:
            full_set = set(result.intermediate_results['home']['full_set'])
        else:
            full_set = set()

        if result.different_timezones is not None:
            if result.different_timezones not in detected_timezones:
                detected_timezones[result.different_timezones] = 0
            detected_timezones[result.different_timezones] += 1

        if contributor.location is None:
            continue

        for item in timezone_evaluations:
            if element_in_string(contributor.location, item['search']):
                survey_string = ', '.join(item['search'])
                if survey_string not in survey_results:
                    survey_results[survey_string] = {}
                    survey_results[survey_string]['set'] = set(home)
                    survey_results[survey_string]['amount'] = 0
                    survey_results[survey_string]['correct'] = 0
                    survey_results[survey_string]['timezone_amount'] = 0
                    survey_results[survey_string]['match'] = item['timezone']
                    survey_results[survey_string]['full_set'] = full_set

                survey_results[survey_string]['set'] = survey_results[survey_string]['set'] | home
                survey_results[survey_string]['amount'] += 1
                survey_results[survey_string]['timezone_amount'] += len(home - ignored_timezones)
                survey_results[survey_string]['ratio'] = survey_results[survey_string]['timezone_amount'] / survey_results[survey_string]['amount']
                considered_contributors += 1

                if 'full_set' in item:
                    survey_results[survey_string]['full_set'] = survey_results[survey_string]['full_set'] | full_set

                # Debug stuff
                if 'roflcopter' == survey_string:
                    print(home)

                if item['timezone'] in home:
                    correct += 1
                    survey_results[survey_string]['correct'] += 1
                break

    logger.info(f'Looked at {len(results)} contributors.')
    logger.info(f'{len(results)} are relevant.')
    logger.info(f'Detected a change in {changed} of those.')
    logger.info(f'Detected no change in {unchanged} of those.')
    logger.info(f'Distribution of users by amount of different timezones:')
    logger.info(pformat(distribution))
    logger.info(f'Distribution of users by amount of detected timezones:')
    logger.info(pformat(detected_timezones))
    logger.info(f'Verified contributors {correct} of {considered_contributors}: {correct/considered_contributors}')

    print(f"Strings query;Considered contributors;Expected timezone;Home location in subset;Mean size of subset;Max size of subset")
    for key, result in survey_results.items():
        print(f"{key};{result['amount']};{result['match']};{result['correct']};{result['ratio']:.2f};{len(result['full_set'])}")

    return


def element_in_string(string, word_list):
    """Check if there is one of the strings in the word list inside the string."""
    for word in word_list:
        # Split by space and check for direct hits.
        # This prevents false positives such as 'NY' to 'nyaaa'.
        if word.lower() in string.lower().split(' '):
            return True

        # If we have something like 'San Fransisco' we cannot split by space.
        if ' ' in word:
            if word.lower() in string.lower():
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
                    or result.timezone_switches is None \
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
                    timezone_set['full_set'] = list(timezone_set['full_set'])

                json_results['home'] = plotter.home_zone
                json_results['travel'] = plotter.data
                result.intermediate_results = json_results

                result.timezone_switches = len(plotter.data)
                result.different_timezones = plotter.different_timezones
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
