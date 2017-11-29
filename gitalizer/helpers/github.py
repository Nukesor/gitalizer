"""Simple wrapper around github that allows for lazy initilization."""
from github import Github as ActualGithub

from gitalizer.config import configs


class Github(object):
    """Github wrapper class that allows for lazy initilization.

    The part about the lazy initilization is important for using Flask with
    application factorties.
    """

    def __init__(self):
        """Initialize github."""
        self.github = ActualGithub(configs['production'].GITHUB_USER,
                                   configs['production'].GITHUB_PASSWORD)

    def init_app(self, app):
        """Lazy initializer which takes an `app` and sets up the internal context."""
        return
