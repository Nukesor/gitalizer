"""Email unknown field

Revision ID: 260052013f65
Revises: e5bc054554c6
Create Date: 2018-02-12 21:06:16.173039

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '260052013f65'
down_revision = 'e5bc054554c6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('commit', 'unknown')
    op.add_column('email', sa.Column('unknown', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('email', 'unknown')
    op.add_column('commit', sa.Column('unknown', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
    # ### end Alembic commands ###