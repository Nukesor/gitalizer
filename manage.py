"""File for commandline manager."""

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from gitalizer import create_app
from gitalizer.extensions import db
from gitalizer.aggregators.github.user import get_user as get_user_data

app = create_app()

migrate = Migrate(app, db)
manager = Manager(app)

# migrations
manager.add_command('db', MigrateCommand)


@manager.command
def create_db():
    """Create the db tables."""
    with app.app_context():
        db.drop_all()
        db.create_all()


@manager.command
def drop_db():
    """Drop the db tables."""
    with app.app_context():
        db.drop_all()


@manager.command
@manager.option('-n', '--name', dest='name', help='Github username')
def get_user(name='Nukesor'):
    """Get the repository for a specific github user."""
    with app.app_context():
        get_user_data(name)


if __name__ == '__main__':
    manager.run()
