"""Simple helper functions."""
import os
from gitalizer.config import configs


def get_config(config_name=None):
    """Return the current config, depending on parameter or environment variable."""
    if config_name is None:
        config_name = os.environ.get('GITALIZER_CONFIG', 'develop')
        return configs[config_name]

    return configs[config_name]
