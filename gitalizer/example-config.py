"""Global project configuration."""
from datetime import timedelta
from pygit2 import GitError


class Config(object):
    """Generic configuration class for default options."""

    DEBUG = False
    TESTING = False
    AUTH_TOKEN_TIMEOUT = timedelta(days=30)
    SENTRY_TOKEN = ''

    GITHUB_USER = 'User'
    GITHUB_PASSWORD = 'userpass'
    GITHUB_TOKEN = None

    SSH_USER = 'git'
    SSH_PASSWORD = 'password'
    PUBLIC_KEY = '/home/user/.ssh/id_rsa.pub'
    PRIVATE_KEY = '/home/user/.ssh/id_rsa'

    GIT_CLONE_PATH = '/tmp/gitalizer'
    GIT_USER_SCAN_THREADS = 4
    GIT_COMMIT_SCAN_THREADS = 4

    MAX_REPOSITORY_SIZE = 1024 * 1024 * 10
    GITHUB_USER_SKIP_COUNT = 3000

    REPOSITORY_RESCAN_TIMEOUT = timedelta(days=5)
    CONTRIBUTER_RESCAN_TIMEOUT = timedelta(days=14)

    SENTRY = False
    SENTRY_CONFIG = {
        'ignore_exceptions': [
            KeyboardInterrupt,
            GitError,
        ],
        'exclude_paths': [
            'plot',
        ],
    }

    PLOT_DIR = './plots'
    LOG_DIR = './logs'

    # Flask-SQLAlchemy options (see http://flask-sqlalchemy.pocoo.org/2.1/config/)
    SQLALCHEMY_DATABASE_URI = 'postgres://localhost/gitalizer'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PASSLIB_SCHEMES = ["argon2"]

    CORS_ALLOW_ORIGIN = '*'
    CORS_ALLOW_METHODS = '*'
    CORS_ALLOW_HEADERS = '*'


class ProductionConfig(Config):
    """Production specific configuration."""

    SERVER_NAME = 'localhost:1337'
    SECRET_KEY = ""


class DevelopConfig(Config):
    """Develop specific configuration."""

    SERVER_NAME = 'localhost:5000'
    SECRET_KEY = ""


class TestingConfig(Config):
    """Testing specific configuration."""

    TESTING = True
    SERVER_NAME = 'localhost:5000'
    SECRET_KEY = """
        neigh6echeih4eiqueetei2ietha1raitooSahzai6ugh0jahzahm
        u2»{1³21igh1saWooshi3uxah4oongiuphiox7iephoonahkoiK9u
    """


configs = {
    'production': ProductionConfig,
    'develop': DevelopConfig,
    'testing': TestingConfig,
}
