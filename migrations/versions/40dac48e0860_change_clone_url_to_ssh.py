"""Change clone_url to ssh

Revision ID: 40dac48e0860
Revises: 13e4e4239706
Create Date: 2018-02-12 16:32:10.618517

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '40dac48e0860'
down_revision = '13e4e4239706'
branch_labels = None
depends_on = None


def upgrade():
    """Convert all clone_urls from https to ssh."""
    conn = op.get_bind()
    conn.execute(
        """
            UPDATE repository
            SET clone_url = replace(clone_url, 'https://github.com/', 'git@github.com:');
        """
    )


def downgrade():
    """Convert all clone_urls from ssh to https."""
    conn = op.get_bind()
    conn.execute(
        """
            UPDATE repository
            SET clone_url = replace(clone_url, 'git@github.com:', 'https://github.com/');
        """
    )
