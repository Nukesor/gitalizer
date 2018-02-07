"""empty message

Revision ID: 1cb6f96a1d8e
Revises: 84261e1711f8
Create Date: 2018-01-23 15:00:53.860391

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cb6f96a1d8e'
down_revision = '84261e1711f8'
branch_labels = None
depends_on = None


def upgrade():
    """Rename a column in both many to many relationship."""
    # Contributer repository rename
    # Drop all old constraints
    op.drop_index('ix_commit_repositories_commit_sha', table_name='commit_repository')
    op.drop_index('ix_commit_repositories_repository_url', table_name='commit_repository')
    op.drop_constraint('commit_repositories_repository_url_fkey', 'commit_repository', type_='foreignkey')
    op.drop_constraint('commit_repositories_repository_url_commit_sha_key', 'commit_repository', type_='unique')

    # Rename and create new constraints
    op.alter_column('commit_repository', 'repository_url', new_column_name='repository_clone_url')
    op.create_index(op.f('ix_commit_repository_commit_sha'), 'commit_repository', ['commit_sha'], unique=False)
    op.create_index(op.f('ix_commit_repository_repository_clone_url'), 'commit_repository', ['repository_clone_url'], unique=False)
    op.create_foreign_key(None, 'commit_repository', 'repository', ['repository_clone_url'], ['clone_url'])
    op.create_unique_constraint(None, 'commit_repository', ['repository_clone_url', 'commit_sha'])

    # Contributer repository rename
    # Drop all old constraints
    op.drop_index('ix_contributer_repositories_contributer_login', table_name='contributer_repository')
    op.drop_index('ix_contributer_repositories_repository_url', table_name='contributer_repository')
    op.drop_constraint('contributer_repositories_repository_url_fkey', 'contributer_repository', type_='foreignkey')
    op.drop_constraint('contributer_repositories_repository_url_contributer_login_key', 'contributer_repository', type_='unique')

    # Rename and create new constraints
    op.alter_column('contributer_repository', 'repository_url', new_column_name='repository_clone_url')
    op.create_index(op.f('ix_contributer_repository_contributer_login'), 'contributer_repository', ['contributer_login'], unique=False)
    op.create_index(op.f('ix_contributer_repository_repository_clone_url'), 'contributer_repository', ['repository_clone_url'], unique=False)
    op.create_foreign_key(None, 'contributer_repository', 'repository', ['repository_clone_url'], ['clone_url'])
    op.create_unique_constraint(None, 'contributer_repository', ['repository_clone_url', 'contributer_login'])


def downgrade():
    """Revert the rename of both many to many relationship."""
    # Contributer repository rename
    # Drop all old constraints
    op.drop_index(op.f('ix_contributer_repository_repository_clone_url'), table_name='contributer_repository')
    op.drop_index(op.f('ix_contributer_repository_contributer_login'), table_name='contributer_repository')
    op.drop_constraint(None, 'contributer_repository', type_='unique')
    op.drop_constraint(None, 'contributer_repository', type_='foreignkey')

    # Rename and create new constraints
    op.alter_column('contributer_repository', 'repository_clone_url', new_column_name='repository_url')
    op.create_index('ix_contributer_repositories_repository_url', 'contributer_repository', ['repository_url'], unique=False)
    op.create_index('ix_contributer_repositories_contributer_login', 'contributer_repository', ['contributer_login'], unique=False)
    op.create_foreign_key('contributer_repositories_repository_url_fkey', 'contributer_repository', 'repository', ['repository_url'], ['clone_url'])
    op.create_unique_constraint('contributer_repositories_repository_url_contributer_login_key', 'contributer_repository', ['repository_url', 'contributer_login'])

    # Contributer repository rename
    # Drop all old constraints
    op.drop_index(op.f('ix_commit_repository_repository_clone_url'), table_name='commit_repository')
    op.drop_index(op.f('ix_commit_repository_commit_sha'), table_name='commit_repository')
    op.drop_constraint(None, 'commit_repository', type_='unique')
    op.drop_constraint(None, 'commit_repository', type_='foreignkey')

    # Rename and create new constraints
    op.alter_column('commit_repository', 'repository_clone_url', new_column_name='repository_url')
    op.create_index('ix_commit_repositories_repository_url', 'commit_repository', ['repository_url'], unique=False)
    op.create_index('ix_commit_repositories_commit_sha', 'commit_repository', ['commit_sha'], unique=False)
    op.create_foreign_key('commit_repositories_repository_url_fkey', 'commit_repository', 'repository', ['repository_url'], ['clone_url'])
    op.create_unique_constraint('commit_repositories_repository_url_commit_sha_key', 'commit_repository', ['repository_url', 'commit_sha'])
