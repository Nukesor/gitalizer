"""Helper functions for github api calls."""
from github.GithubException import RateLimitExceededException, GithubException

import time
from random import randrange
from socket import timeout
from datetime import datetime, timedelta
from gitalizer.extensions import github


def call_github_function(github_object: object, function_name: str, args: list=None, kwargs: dict=None):
    """Call a pygithub object member function.

    We need to handle those calls in case we get rate limited.
    """
    _try = 0
    tries = 3
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
            resettime = github.github.get_rate_limit().rate.reset
            delta = resettime - datetime.now()
            delta += timedelta(minutes=2)
            total_minutes = int(delta.total_seconds() / 60)
            print('Hit the rate limit.')
            print(f'Reset at {resettime}. Waiting for {total_minutes} minutes.')
            time.sleep(delta.total_seconds())

            _try += 1
            exception = e
            pass
        except GithubException as e:
            seconds = randrange(180, 300)
            print('GithubException. Probably abuse detection.')
            print(f'Waiting for {seconds} seconds')
            time.sleep(seconds)

            _try += 1
            exception = e
            pass
        except timeout as e:
            print('Hit socket timeout waiting 10 secs.')
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
    tries = 3
    exception = None
    while _try <= tries:
        try:
            retrieved_object = getattr(github_object, object_name)
            return retrieved_object
        except RateLimitExceededException as e:
            # Wait until the rate limiting is reset
            resettime = github.github.get_rate_limit().rate.reset
            delta = resettime - datetime.now()
            delta += timedelta(minutes=2)
            total_minutes = int(delta.total_seconds() / 60)
            print('Hit the rate limit.')
            print(f'Reset at {resettime}. Waiting for {total_minutes} minutes.')

            time.sleep(delta.total_seconds())

            _try += 1
            exception = e
            pass
        except timeout as e:
            print('Hit socket timeout waiting 10 secs.')
            _try += 1
            exception = e
            pass

    raise exception
