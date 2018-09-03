"""DB cli interface."""
import click
from sqlalchemy_utils.functions import (
    database_exists,
    create_database,
    drop_database,
)

from gitalizer.models import (
    TimezoneInterval,
)
from gitalizer.extensions import db as real_db
from gitalizer.timezone.database import create_timezone_database


@click.group()
def db():
    """DB subcommand base."""
    pass


@db.command()
def initdb():
    """Initialize the database.

    This will drop and recreate the actual database if it already exists.
    The database name from the config is used
    variable is used for this.
    """
    # If there is an existing DB, make sure to drop it and start completely fresh.
    db_url = real_db.engine.url
    if database_exists(db_url):
        drop_database(db_url)
    create_database(db_url)

    real_db.Model.metadata.create_all()
    session = real_db.session
    create_timezone_database(session)
    session.commit()


@db.command()
def build_time_db():
    """Drop and recreate all utc offset timeinterval database entries."""
    real_db.create_all()

    session = real_db.new_session()
    session.query(TimezoneInterval).delete()
    create_timezone_database(session)
    session.commit()
    session.close()
