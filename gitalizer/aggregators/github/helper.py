"""Handy helper for the github v3 api."""
import socket


def get_commit_count(contributors):
    """Return the amount of commits in a repository by their contributors."""
    received = False
    while not received:
        try:
            count = 0
            for contributer in contributors:
                count += contributer.contributions
            return count
        except socket.timeout:
            pass
