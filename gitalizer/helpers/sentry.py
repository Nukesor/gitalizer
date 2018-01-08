"""Simple wrapper around sentry that allows for lazy initilization."""
from raven.contrib.flask import Sentry as OriginSentry


class Sentry(object):
    """Sentry wrapper class that allows for lazy initilization.

    The part about the lazy initilization is important for using Flask with
    application factorties.
    """

    def init_app(self, app):
        """Lazy initializer which takes an `app` and sets up sentry."""
        self.sentry = OriginSentry(app, dsn=app.config['SENTRY_TOKEN'])
