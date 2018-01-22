"""This module extends the `flask` command with various `click` subcommands."""

import sys
import click
import urllib.parse
from flask import url_for
from sqlalchemy_utils.functions import database_exists, create_database, drop_database

from gitalizer.plot import plot_user as plot_user_func
from gitalizer.extensions import db
from gitalizer.models.user import User
from gitalizer.helpers.hotfixes import (
    clean_db,
    complete_data,
    migrate as migrate_data,
)
from gitalizer.aggregator.github.repository import (
    get_github_repository_by_owner_name,
    get_github_repository_users,
)
from gitalizer.aggregator.github.organization import (
    get_github_organization,
    get_github_organizations,
)
from gitalizer.aggregator.github.user import (
    get_user_by_name,
    get_friends_by_name,
)


def register_cli(app):  # pragma: no cover
    """Register a few CLI functions."""
    @app.cli.command()
    def url_map():
        """Print the URL map."""
        output = []
        for rule in app.url_map.iter_rules():

            options = {}
            for arg in rule.arguments:
                options[arg] = "[{0}]".format(arg)

            methods = ','.join(rule.methods)
            url = url_for(rule.endpoint, **options)
            line = urllib.parse.unquote("{endpoint:50s} {methods:20s} {url}".format(
                endpoint=rule.endpoint,
                methods=methods,
                url=url),
            )
            output.append(line)

        for line in sorted(output):
            click.echo(line)

    @app.cli.command()
    def initdb():
        """Initialize the database.

        This will drop and recreate the actual database if it already exists.
        The database name from the config is used
        variable is used for this.
        """
        # If there is an existing DB, make sure to drop it and start completely fresh.
        db_url = db.engine.url
        if database_exists(db_url):
            drop_database(db_url)
        create_database(db_url)

        db.create_all()

        user = User("test@example.com", "test")
        db.session.add(user)
        db.session.commit()

    @app.cli.command()
    @click.argument('name')
    def get_user(name):
        """Get all repositories for a specific github user."""
        try:
            app.logger.info(f'\n\nGet user {name}')
            get_user_by_name(name)
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('name')
    def get_friends(name):
        """Get the repositories of a user and all his friends."""
        try:
            app.logger.info(f'\n\nGet friends of user {name}')
            get_friends_by_name(name)
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('owner')
    @click.argument('repository')
    def get_github_repository(owner, repository):
        """Get a github repository by owner and name."""
        try:
            app.logger.info(f'\n\nGet {repository} from user {owner}')
            get_github_repository_by_owner_name(owner, repository)
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('full_name')
    def get_repository_users(full_name):
        """Get a github repository by owner and name."""
        try:
            app.logger.info(f'\n\nGet users from {full_name}')
            get_github_repository_users(full_name)
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('orga')
    def get_organization(orga):
        """Get github organizations for all known contributers."""
        try:
            get_github_organization(orga)
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    def get_organizations():
        """Get github organizations for all known contributers."""
        try:
            get_github_organizations()
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('owner')
    def plot_user(owner):
        """Plot all graphs for a specific github user."""
        try:
            plot_user_func(owner)
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    def clean():
        """Plot all graphs for a specific github user."""
        try:
            clean_db()
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    def complete():
        """Complete missing data from previous runs."""
        try:
            complete_data()
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    def migrate():
        """Migrate data in case of significant schema changes."""
        try:
            migrate_data()
        except KeyboardInterrupt:
            print("CTRL-C Exiting Gracefully")
            sys.exit(1)
