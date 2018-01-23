"""A new many to many relationship between commits and repositories.

Revision ID: 5a8fbf49bbb9
Revises: 7b96a74c6645
Create Date: 2018-01-23 00:52:09.322867

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


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

    # Copy data into new many to many relationship
    conn = op.get_bind()
    conn.execute(
        text("""
            INSERT INTO commit_repositories
            SELECT sha, repository_url
            FROM commit;
    """))

    conn.execute(
        text("""
        DELETE
        FROM commit a
        USING commit b
        WHERE
            a.id < b.id
        AND
            a.sha = b.sha;
    """))

    # Create new commit unique constraint
    op.create_unique_constraint(None, 'commit', ['sha'])

    # Create commit_repository data and constraints
    op.create_foreign_key(None, 'commit_repositories', 'commit', ['commit_sha'], ['sha'])
    op.create_foreign_key(None, 'commit_repositories', 'repository', ['repository_url'], ['clone_url'])
    op.create_unique_constraint(None, 'commit_repositories', ['repository_url', 'commit_sha'])

    # Drop old repository url data and constraints.
    op.drop_index('ix_commit_repository_url', table_name='commit')
    op.drop_constraint('commit_sha_repository_url_key', 'commit', type_='unique')
    op.drop_constraint('commit_repository_url_fkey', 'commit', type_='foreignkey')

    # Drop old repository_url as the data is now in commit_repositories
    op.drop_column('commit', 'repository_url')


def downgrade():
    """Downgrade."""
    # Drop all constraints and indices of the new table
    op.drop_constraint(None, 'commit_repositories', type_='foreignkey')
    op.drop_constraint(None, 'commit_repositories', type_='foreignkey')
    op.drop_constraint(None, 'commit_repositories', type_='unique')
    op.drop_index(op.f('ix_commit_repositories_repository_url'), table_name='commit_repositories')
    op.drop_index(op.f('ix_commit_repositories_commit_sha'), table_name='commit_repositories')
    op.drop_constraint(None, 'commit', type_='unique')

    # Do stuff:
    op.drop_table('commit_repositories')

    # Create old columns
    op.add_column('commit', sa.Column('repository_url', sa.VARCHAR(length=240), autoincrement=False, nullable=False))

    # Create old constraints and indices
    op.create_index('ix_commit_repository_url', 'commit', ['repository_url'], unique=False)
    op.create_unique_constraint('commit_sha_repository_url_key', 'commit', ['sha', 'repository_url'])
    op.create_foreign_key('commit_repository_url_fkey', 'commit', 'repository', ['repository_url'], ['clone_url'], ondelete='CASCADE')
