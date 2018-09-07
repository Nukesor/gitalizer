"""Configuration Reader."""
import os
import sys
import configparser


def read_config():
    """Read a previous configuration file or create a new with default values."""
    path = os.path.expanduser('~/.config/gitalizer.ini')
    path = os.path.realpath(path)
    config = configparser.ConfigParser()
    # Try to get configuration file and return it
    # If this doesn't work, a new default config file will be created
    if os.path.exists(path):
        try:
            config.read(path)
            return config
        except Exception:
            print('Error while parsing config file')
            raise Exception

    config['develop'] = {
        'log_dir': './logs',
        'sentry_token': '',
        'sentry_enabled': 'no',
    }
    config['github'] = {
        'github_user': 'git',
        'github_password': '',
        'github_token': '',
    }
    config['cloning'] = {
        'ssh_user': '',
        'ssh_password': '',
        'private_key': '/home/user/.ssh/id_rsa',
        'public_key': '/home/user/.ssh/id_rsa.pub',
        'temporary_clone_path': '/tmp/gitalizer',
    }
    config['aggregator'] = {
        'git_user_scan_threads': 4,
        'git_commit_scan_threads': 4,
        'max_repository_size': 4 * 1024 * 1024,
        'max_repositories_for_user': 3000,
        'repository_rescan_interval': 21 * 24 * 60 * 60,
        'contributor_rescan_interval': 22 * 24 * 60 * 60,
    }

    config['database'] = {
        'uri': 'postgres://localhost/gitalizer',
        'echo': 'no',
    }
    config['plotting'] = {
        'plot_dir': './plots',
    }

    with open(path, 'w') as fd:
        config.write(fd)

    print('Initialized empty configuration. Please adjust before proceeding.')
    sys.exit(0)


config = read_config()
