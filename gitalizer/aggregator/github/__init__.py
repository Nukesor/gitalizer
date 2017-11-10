"""Helper functions for github api calls."""
from github.GithubException import RateLimitExceededException

import time
import datetime
from gitalizer.extensions import github


def call_github_function(github_object: object, function_name: str, args: list):
    """Call a pygithub object member function.

    We need to handle those calls in case we get rate limited.
    """
    _try = 0
    tries = 3
    exception = None
    while _try <= tries:
        try:
            retrieved_object = getattr(github_object, function_name)(*args)
            return retrieved_object
        except RateLimitExceededException as e:
            # Wait until the rate limiting is reset
            resettime = github.rate_limiting_resettime
            resettime = datetime.datetime.fromtimestamp(resettime)
            delta = resettime - datetime.now()
            delta += datetime.timedelta(minutes=1)
            total_minutes = int(delta.total_seconds() / 60)
            print(f'Hit the rate limit. Waiting for {total_minutes} seconds')
            time.sleep(delta.total_seconds())

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
            resettime = github.rate_limiting_resettime
            resettime = datetime.datetime.fromtimestamp(resettime)
            delta = resettime - datetime.now()
            delta += datetime.timedelta(minutes=1)
            total_minutes = int(delta.total_seconds() / 60)
            print(f'Hit the rate limit. Waiting for {total_minutes} seconds')
            time.sleep(delta.total_seconds())

            _try += 1
            exception = e
            pass

    raise exception
