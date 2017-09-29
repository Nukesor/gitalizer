import os
import unittest

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from gitalizer import create_app
from gitalizer.extensions import db

app = create_app()

migrate = Migrate(app, db)
manager = Manager(app)

# migrations
manager.add_command('db', MigrateCommand)


@manager.command
def create_db():
    """Creates the db tables."""
    with app.app_context():
        db.create_all()


@manager.command
def drop_db():
    """Drops the db tables."""
    with app.app_context():
        db.drop_all()


if __name__ == '__main__':
    manager.run()
