"""Base command for gitalizer."""
import click
from .db import db
from .delete import delete
from .maintenance import maintenance
from .organization import organization
from .user import user
from .repository import repository


@click.group()
def cli():
    """Init function for gitalizer."""
    pass


@click.group()
def scan():
    """Init function for gitalizer."""
    pass


cli.add_command(db)
cli.add_command(scan)
cli.add_command(delete)
cli.add_command(maintenance)

scan.add_command(user)
scan.add_command(repository)
scan.add_command(organization)
