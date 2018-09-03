"""DB maintenance operations."""

import sys
import click

from gitalizer.extensions import logger
from gitalizer.helpers.db.maintenance import (
    clean_db,
    complete_data,
    update_data,
)


@click.group()
def maintenance():
    """Cli wrapper for the maintenance command group."""
    pass


@click.command()
def clean():
    """Remove uncomplete or unwanted data.

    This includes:
        - Duplicate commits from forked repositories (Shouldn't happen any longer).
        - Dangling commits (Shouldn't happen any longer).
    """
    try:
        clean_db()
    except KeyboardInterrupt:
        sys.exit(1)


@click.command()
def complete():
    """Complete missing data from previous runs.

    This includes:
        - Complete all unfinished repositories
    """
    try:
        complete_data()
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)


@click.command()
@click.option('--update-all', default=False, help='Scan EVERYTHING again.')
def update(update_all):
    """Update data from previous runs.

    If the `--update-all` flag is provided, everything will be scanned again.
    For instance, without the flag, only contributors with more than 100 commits will be scanned.
    This prevents scans of users which might be uninteresting peers and, for instance, only have one commit in a uninteresting repository.

    This includes:
        - Update all contributors
    """
    try:
        update_data(update_all)
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)


maintenance.add_command(clean)
maintenance.add_command(complete)
maintenance.add_command(update)
