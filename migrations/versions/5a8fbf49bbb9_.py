"""A new many to many relationship between commits and repositories.

Revision ID: 5a8fbf49bbb9
Revises: 7b96a74c6645
Create Date: 2018-01-23 00:52:09.322867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a8fbf49bbb9'
down_revision = '7b96a74c6645'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade."""
    # Create new table
    op.create_table(
        'commit_repositories',
        sa.Column('commit_sha', sa.String(length=40), nullable=True),
        sa.Column('repository_url', sa.String(length=240), nullable=True),
    )
    op.create_index(op.f('ix_commit_repositories_commit_sha'), 'commit_repositories', ['commit_sha'], unique=False)
    op.create_index(op.f('ix_commit_repositories_repository_url'), 'commit_repositories', ['repository_url'], unique=False)

    # Drop old table.
    op.drop_index('ix_commit_repository_url', table_name='commit')
    op.drop_constraint('commit_sha_repository_url_key', 'commit', type_='unique')
    op.drop_constraint('commit_repository_url_fkey', 'commit', type='foreignkey')
    # ### end Alembic commands ###


def downgrade():
    """Downgrade."""
    # First drop the newly created table.
    op.drop_index(op.f('ix_commit_repositories_repository_url'), table_name='commit_repositories')
    op.drop_index(op.f('ix_commit_repositories_commit_sha'), table_name='commit_repositories')
    op.drop_table('commit_repositories')

    op.create_foreign_key('commit_repository_url_fkey', 'commit', 'repository', ['repository_url'], ['clone_url'], ondelete='CASCADE')
    op.create_index('ix_commit_repository_url', 'commit', ['repository_url'], unique=False)
    op.create_unique_constraint('commit_sha_repository_url_key', 'commit', ['sha', 'repository_url'])
