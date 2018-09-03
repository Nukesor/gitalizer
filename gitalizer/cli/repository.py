"""Repository scanning cli."""
import sys
import click

from gitalizer.extensions import logger
from gitalizer.aggregator.github.repository import (
    get_github_repository_by_owner_name,
    get_github_repository_users,
)


@click.group()
def repository():
    """Scan repositories."""
    pass


@click.command()
@click.argument('owner')
@click.argument('repository')
def from_github(owner, repository):
    """Get a github repository by owner and name."""
    try:
        logger.info(f'\n\nGet {repository} from user {owner}')
        get_github_repository_by_owner_name(owner, repository)
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)


@click.command()
@click.argument('full_name')
def from_github_for_users(full_name):
    """Scan all users of a github repository."""
    try:
        logger.info(f'\nGet all users from {full_name}')
        get_github_repository_users(full_name)
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)


repository.add_command(from_github)
repository.add_command(from_github_for_users)
