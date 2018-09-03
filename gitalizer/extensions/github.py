"""Simple wrapper around github that allows for lazy initilization."""
from github import Github as ActualGithub


class Github(object):
    """Github wrapper class that allows single initialization."""

    def __init__(self, config):
        """Initialize github."""
        if config.GITHUB_TOKEN:
            user = config.GITHUB_TOKEN
            password = None
        else:
            user = config.GITHUB_USER
            password = config.GITHUB_PASSWORD
        self.github = ActualGithub(user, password)
