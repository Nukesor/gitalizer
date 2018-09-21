"""Helper functions for github api calls."""
from github.GithubException import RateLimitExceededException, GithubException

import time
from socket import timeout
from random import randrange
from raven import breadcrumbs
from datetime import datetime, timedelta

from gitalizer.extensions import github, logger


def call_github_function(github_object: object, function_name: str,
                         args: list = None, kwargs: dict = None):
    """Call a pygithub object member function.

    We need to handle those calls in case we get rate limited.
    """
    _try = 0
    tries = 5
    exception = None
    while _try <= tries:
        try:
            if not args:
                args = []
            if not kwargs:
                kwargs = {}
            retrieved_object = getattr(github_object, function_name)(*args, **kwargs)
            return retrieved_object
        except RateLimitExceededException as e:
            # Wait until the rate limiting is reset
            resettime = github.github.get_rate_limit().core.reset
            if resettime < datetime.now():
                resettime = datetime.now()
            delta = resettime - datetime.utcnow()
            delta += timedelta(minutes=2)
            total_minutes = int(delta.total_seconds() / 60)
            logger.info('Hit the rate limit.')
            logger.info(f'Reset at {resettime}. Waiting for {total_minutes} minutes.')
            time.sleep(delta.total_seconds())

            _try += 1
            exception = e
            pass
        except GithubException as e:
            # Forbidden or not found (Just made private or deleted)
            if e.status == 451 or e.status == 404:
                raise e

                # Otherwise abuse detection
            if e.status == 403:
                seconds = randrange(180, 480)
                logger.info('Github abuse detection.')
                logger.info(f'Waiting for {seconds} seconds')
                time.sleep(seconds)

            breadcrumbs.record(
                data={'action': 'Github Exception.', 'exception': e},
                category='info',
            )

            _try += 1
            exception = e
            pass
        except timeout as e:
            logger.info('Hit socket timeout waiting 10 secs.')
            breadcrumbs.record(data={'action': 'Socket timeout hit'},
                               category='info')

            time.sleep(10)
            _try += 1
            exception = e
            pass

    raise exception


def get_github_object(github_object: object, object_name: str):
    """Get a pygithub object.

    As pygithub sometimes implicitly queries the github api on a class member access,
    we need to handle those accesses in case we get rate limited.
    """
    _try = 0
    tries = 5
    exception = None
    while _try <= tries:
        try:
            retrieved_object = getattr(github_object, object_name)
            return retrieved_object
        except RateLimitExceededException as e:
            # Wait until the rate limiting is reset
            resettime = github.github.get_rate_limit().core.reset
            if resettime < datetime.now():
                resettime = datetime.now()
            delta = resettime - datetime.now()
            delta += timedelta(minutes=2)
            total_minutes = int(delta.total_seconds() / 60)
            logger.info('Hit the rate limit.')
            logger.info(f'Reset at {resettime}. Waiting for {total_minutes} minutes.')

            time.sleep(delta.total_seconds())

            _try += 1
            exception = e
            pass
        except GithubException as e:
            # Forbidden or not found (Just made private or deleted)
            if e.status == 451 or e.status == 404:
                raise e

                # Otherwise abuse detection
            if e.status == 403:
                seconds = randrange(180, 480)
                logger.info('Github abuse detection.')
                logger.info(f'Waiting for {seconds} seconds')
                time.sleep(seconds)

            breadcrumbs.record(
                data={'action': 'Github Exception.', 'exception': e},
                category='info',
            )

            _try += 1
            exception = e
            pass
        except timeout as e:
            logger.info('Hit socket timeout waiting 10 secs.')
            breadcrumbs.record(data={'action': 'Socket timeout hit'},
                               category='info')

            time.sleep(10)
            _try += 1
            exception = e
            pass

    raise exception
