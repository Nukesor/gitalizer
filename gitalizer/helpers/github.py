"""Simple wrapper around github that allows for lazy initilization."""
from github import Github as ActualGithub


class Github(object):
    """Github wrapper class that allows for lazy initilization.

    The part about the lazy initilization is important for using Flask with
    application factorties.
    """

    def init_app(self, app):
        """Lazy initializer which takes an `app` and sets up the internal context."""
        self.github = ActualGithub(app.config['GITHUB_USER'],
                                   app.config['GITHUB_PASSWORD'])
