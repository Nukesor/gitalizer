"""Handy helper for the github v3 api."""


def get_commit_count(contributors):
    """Return the amount of commits in a repository by their contributors."""
    count = 0
    for contributer in contributors:
        count += contributer.contributions
    return count
