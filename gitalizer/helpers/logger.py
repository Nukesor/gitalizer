"""Logger class."""
import os
import sys
import logging

from logging.handlers import RotatingFileHandler


def init_logging(config):
    """Create log directory and initialize logger."""
    # Create log directory, if it doesn't exist
    logger = logging.getLogger('gitalizer')
    log_dir = config.LOG_DIR
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger.setLevel(logging.INFO)

    # Initialize log file for daemon output
    daemon_log_path = os.path.join(log_dir, 'gitalizer.log')

    log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add a handler which outputs the log to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_format)
    logger.addHandler(stdout_handler)

    # Add a handler which outputs to a logfile
    file_handler = RotatingFileHandler(
        daemon_log_path,
        maxBytes=(1048576*5),
        backupCount=7,
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger
