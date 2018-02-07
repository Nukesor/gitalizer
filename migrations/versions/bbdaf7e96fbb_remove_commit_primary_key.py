"""New commit primary key.

Revision ID: bbdaf7e96fbb
Revises: 9c23829e6ef9
Create Date: 2018-02-07 14:02:11.588133

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'bbdaf7e96fbb'
down_revision = '9c23829e6ef9'
branch_labels = None
depends_on = None


def upgrade():
    """Drop id primary key and use sha as pkey."""
    op.drop_constraint('commit_repository_commit_sha_fkey', 'commit_repository', type_='foreignkey')
    op.drop_constraint('commit_pkey', 'commit', type_='primary')
    op.drop_constraint('commit_sha_key', 'commit', type_='unique')
    op.create_primary_key('commit_pkey', 'commit', ['sha'])
    op.create_foreign_key('commit_repository_commit_sha_fkey', 'commit_repository', 'commit', ['commit_sha'], ['sha'])
    op.drop_column('commit', 'id')


def downgrade():
    """Drop sha primary key and create id uuid pkey."""
    op.drop_constraint('commit_repository_commit_sha_fkey', 'commit_repository', type_='foreignkey')
    op.drop_constraint('commit_pkey', 'commit', type_='primary')
    op.add_column('commit', sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False, server_default=text('uuid_generate_v4()')))
    op.create_unique_constraint('commit_sha_key', 'commit', ['sha'])
    op.create_primary_key('commit_pkey', 'commit', ['id'])
    op.create_foreign_key('commit_repository_commit_sha_fkey', 'commit_repository', 'commit', ['commit_sha'], ['sha'])
