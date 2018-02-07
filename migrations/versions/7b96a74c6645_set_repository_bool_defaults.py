"""Initial migration

Revision ID: 7b96a74c6645
Revises:
Create Date: 2018-01-23 00:31:32.427167

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b96a74c6645'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade initial migration."""
    op.alter_column(
        'contributer', 'too_big',
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text('false'),
    )
    op.alter_column(
        'repository', 'broken',
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text('false'),
    )
    op.alter_column(
        'repository', 'completely_scanned',
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text('false'),
    )
    op.alter_column(
        'repository', 'fork',
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text('false'),
    )


def downgrade():
    """Downgrade initial migration."""
    op.alter_column(
        'repository', 'fork',
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default=sa.text('false'),
    )
    op.alter_column(
        'repository', 'completely_scanned',
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    op.alter_column(
        'repository', 'broken',
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default=sa.text('false'),
    )
    op.alter_column(
        'contributer', 'too_big',
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default=sa.text('false'),
    )
