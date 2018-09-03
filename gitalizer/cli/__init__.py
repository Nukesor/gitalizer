"""Base command for gitalizer."""
import click
from .db import db
from .user import user


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

scan.add_command(user)
