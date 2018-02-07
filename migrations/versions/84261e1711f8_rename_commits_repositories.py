"""Rename commit_repositories to commit_repository.

Revision ID: 84261e1711f8
Revises: 5a8fbf49bbb9
Create Date: 2018-01-23 14:55:14.387838

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '84261e1711f8'
down_revision = '5a8fbf49bbb9'
branch_labels = None
depends_on = None


def upgrade():
    """Rename tables."""
    op.rename_table('commit_repositories', 'commit_repository')
    op.rename_table('contributer_repositories', 'contributer_repository')


def downgrade():
    """Revert renaming."""
    op.rename_table('commit_repository', 'commit_repositories')
    op.rename_table('contributer_repository', 'contributer_repositories')
