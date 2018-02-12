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
        if configs['production'].GITHUB_TOKEN:
            user = configs['production'].GITHUB_TOKEN
            password = None
        else:
            user = configs['production'].GITHUB_USER
            password = configs['production'].GITHUB_PASSWORD
        self.github = ActualGithub(user, password)

    def init_app(self, app):
        """Lazy initializer which takes an `app` and sets up the internal context."""
        return
