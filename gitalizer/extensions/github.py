"""Simple wrapper around github that allows for lazy initilization."""
from github import Github as ActualGithub


class Github(object):
    """Github wrapper class that allows single initialization."""

    def __init__(self, config):
        """Initialize github."""
        if config['github']['github_token']:
            user = config['github']['github_token']
            password = None
        else:
            user = config['github']['github_user']
            password = config['github']['github_password']
        self.github = ActualGithub(user, password)
