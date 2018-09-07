"""Simple wrapper around sentry that allows for lazy initilization."""
from pygit2 import GitError
from raven import Client


class Sentry(object):
    """Sentry wrapper class that allows this app to work without a sentry token.

    If no token is specified in the config, the messages used for logging are simply not called.
    """

    initialized = False

    def __init__(self, config):
        """Construct new sentry wrapper."""
        if config['develop']['sentry_token'] is not None \
                and config['develop'].getboolean('sentry_enabled'):
            self.initialized = True
            self.sentry = Client(
                config['develop']['sentry_token'],
                ignore_exceptions=[
                    KeyboardInterrupt,
                    GitError,
                ],
            )

    def captureMessage(self, *args, **kwargs):
        """Capture message with sentry."""
        if self.initialized:
            self.sentry.captureMessage(*args, **kwargs)

    def captureException(self, *args, **kwargs):
        """Capture exception with sentry."""
        if self.initialized:
            self.sentry.captureException(*args, **kwargs)
