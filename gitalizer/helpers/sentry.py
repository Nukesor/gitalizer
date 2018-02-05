"""Simple wrapper around sentry that allows for lazy initilization."""
from raven.contrib.flask import Sentry as OriginSentry


class Sentry(object):
    """Sentry wrapper class that allows for lazy initilization.

    The part about the lazy initilization is important for using Flask with
    application factorties.
    """
    initialized = False

    def init_app(self, app):
        """Lazy initializer which takes an `app` and sets up sentry."""
        self.initialized = True
        self.sentry = OriginSentry(app, dsn=app.config['SENTRY_TOKEN'])

    def captureMessage(self, *args, **kwargs):
        """Capture message with sentry."""
        if self.initialized:
            self.sentry.captureMessage(*args, **kwargs)

    def captureException(self, *args, **kwargs):
        """Capture exception with sentry."""
        if self.initialized:
            self.sentry.captureException(*args, **kwargs)
