"""User scan."""
import sys
import click
from gitalizer.extensions import logger
from gitalizer.aggregator.github.user import (
    get_user,
    get_user_with_followers,
)


@click.command()
@click.argument('login')
@click.option('--with-followers', default=False, help='If true, not only the user but all followers and following will be scanned.')
def user(login, with_followers):
    """Get all repositories for a specific github user.

    If `--with-followers` is provided, the user and ALL of his followers/following will be scanned.
    This is recommended for a better coverage, but it will also take significantly longer and require significantly more disk space.
    """
    try:
        if with_followers:
            logger.info(f'\n\nGet friends of user {login}')
            get_user_with_followers(login)
        else:
            logger.info(f'\n\nGet user {login}')
            get_user(login)
    except KeyboardInterrupt:
        logger.info("CTRL-C Exiting Gracefully")
        sys.exit(1)
