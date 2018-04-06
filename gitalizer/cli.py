"""This module extends the `flask` command with various `click` subcommands."""

import sys
import click
import urllib.parse
from flask import url_for
from sqlalchemy_utils.functions import (
    database_exists,
    create_database,
    drop_database,
)

from gitalizer.extensions import db
from gitalizer.plot import (
    plot_user as plot_user_func,
    plot_employee,
    plot_comparison as plot_comparison_func,
)
from gitalizer.timezone.database import create_timezone_database
from gitalizer.models import (
    Commit,
    commit_repository,
    Repository,
    TimezoneInterval,
    User,
)
from gitalizer.helpers.hotfixes import (
    clean_db,
    complete_data,
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
    get_user_by_login,
    get_friends_by_name,
)
from gitalizer.analysis import (
    analyse_travel_path,
    analyse_punch_card,
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
        db.session.commit()

    @app.cli.command()
    def rebuild_time_db():
        """Drop and recreate all utc offset timeinterval database entries."""
        db.create_all()

        db.session.query(TimezoneInterval).delete()
        create_timezone_database()
        db.session.commit()

    @app.cli.command()
    @click.argument('login')
    def get_user(login):
        """Get all repositories for a specific github user."""
        try:
            app.logger.info(f'\n\nGet user {login}')
            get_user_by_login(login)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('name')
    def get_friends(name):
        """Get the repositories of a user and all his friends."""
        try:
            app.logger.info(f'\n\nGet friends of user {name}')
            get_friends_by_name(name)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
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
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('full_name')
    def get_repository_users(full_name):
        """Get a github repository by owner and name."""
        try:
            app.logger.info(f'\n\nGet users from {full_name}')
            get_github_repository_users(full_name)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('orga')
    def get_organization(orga):
        """Get github organizations for all known contributors."""
        try:
            get_github_organization(orga)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('orga')
    def get_organization_with_member(orga):
        """Get github organizations for all known contributors."""
        try:
            get_github_organization(orga, True)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    def get_organizations():
        """Get github organizations for all known contributors."""
        try:
            get_github_organizations()
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    # ----- Plotting / Data mining -----

    @app.cli.command()
    @click.argument('login')
    def plot_user(login):
        """Plot all graphs for a specific github user."""
        try:
            plot_user_func(login)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('login')
    @click.argument('repositories', nargs=-1)
    def plot_user_for_repositories(login, repositories):
        """Get statistics of an user for specific repositories."""
        try:
            plot_employee(login, repositories)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('logins')
    @click.argument('repositories', nargs=-1)
    def plot_comparison(logins, repositories):
        """Get statistics of several user for specific repositories."""
        # The logins are comma seperated ('test1,test2,rofl,wtf,omfg')
        try:
            plot_comparison_func(logins, repositories)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    # ----- Analysis -------
    @app.cli.command()
    def analyse_travel():
        """Analyse missing time stuff."""
        try:
            analyse_travel_path()
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.option('--existing/-e', default=False)
    def analyse_punch(existing):
        """Analyse missing time stuff."""
        try:
            for method in ['mean-shift', 'affinity']:
                if method == 'dbscan':
                    for min_samples in range(5, 10, 5):
                        for eps in range(140, 150, 2):
                            analyse_punch_card(
                                existing, method,
                                eps=eps, min_samples=min_samples,
                            )
                else:
                    analyse_punch_card(existing, method)
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    # ----- Maintainance -----

    @app.cli.command()
    def clean():
        """Remove uncomplete or unwanted data."""
        try:
            clean_db()
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    def test():
        """Complete missing data from previous runs."""
        try:
            from gitalizer.models import Contributor
            from gitalizer.plot.user import plot_user_travel_path
            contributor = db.session.query(Contributor) \
                .filter(Contributor.login.ilike('Nukesor')) \
                .one_or_none()

            plot_user_travel_path(contributor, './')
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    def complete():
        """Complete missing data from previous runs."""
        try:
            complete_data()
        except KeyboardInterrupt:
            app.logger.info("CTRL-C Exiting Gracefully")
            sys.exit(1)

    @app.cli.command()
    @click.argument('owner')
    @click.argument('repository')
    def profile(owner, repository):
        """Profile the get of a specific function."""
        import cProfile, pstats, io
        pr = cProfile.Profile()
        pr.enable()
        get_github_repository_by_owner_name(owner, repository)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        app.logger.info(s.getvalue())

    @app.cli.command()
    @click.argument('full_name')
    def delete_repository(full_name):
        """Profile the get of a specific function."""
        repository = db.session.query(Repository) \
            .filter(Repository.full_name == full_name) \
            .one()

        commit_shas = db.session.query(Commit.sha) \
            .join(
                commit_repository,
                commit_repository.c.repository_clone_url == repository.clone_url,
            ) \
            .filter(commit_repository.c.commit_sha == Commit.sha) \
            .all()

        commit_shas = [c[0] for c in commit_shas]
        if commit_shas:
            db.session.query(Commit) \
                .filter(Commit.sha.in_(commit_shas)) \
                .delete(synchronize_session=False)

        db.session.query(Repository) \
            .filter(Repository.full_name == full_name) \
            .delete()
        db.session.commit()
