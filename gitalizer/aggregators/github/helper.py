"""Handy helper for the github v3 api."""
import socket


def get_commit_count(contributors):
    """Return the amount of commits in a repository by their contributors."""
    _try = 0
    tries = 3
    while _try <= tries:
        try:
            count = 0
            for contributer in contributors:
                count += contributer.contributions
            return count
        except socket.timeout:
            print(f'Failed to receive contributors. Try {_try} of {tries}')
            pass
    raise Exception
