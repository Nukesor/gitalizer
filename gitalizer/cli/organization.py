"""Organization scanning cli."""
import sys
import click

from gitalizer.extensions import logger

from gitalizer.aggregator.github.organization import (
    get_github_organization,
    get_organization_memberships,
)


@click.group()
def organization():
    """Scan repositories."""
    pass


@click.command()
@click.argument('name')
def by_name(name):
    """Get github organizations for all known contributors."""
    try:
        logger.info(f'\nGet organization {name}')
        get_github_organization(name)
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)


@click.command()
@click.argument('name')
def members(name):
    """Scan all members of a organization."""
    try:
        get_github_organization(name, True)
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)


@click.command()
def user_membership():
    """Get all organizations for all known users (users in current database).

    This operation only scans the membership of users and doesn't scan any repositories.
    It is not yet multi processed.
    """
    try:
        get_organization_memberships()
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)


organization.add_command(by_name)
organization.add_command(members)
organization.add_command(user_membership)
