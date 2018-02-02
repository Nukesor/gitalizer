"""empty message

Revision ID: 3e28f27eda85
Revises: b0876060d7cf
Create Date: 2018-02-02 11:16:26.739353

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3e28f27eda85'
down_revision = 'b0876060d7cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contributer', sa.Column('last_full_scan', sa.DateTime(timezone=True), nullable=True))
    op.drop_column('contributer', 'last_check')
    op.drop_column('contributer', 'full_scan')
    op.add_column('repository', sa.Column('too_big', sa.Boolean(), server_default='FALSE', nullable=False))
    op.alter_column('repository', 'completely_scanned', server_default='FALSE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('repository', 'too_big')
    op.add_column('contributer', sa.Column('full_scan', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('contributer', sa.Column('last_check', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.drop_column('contributer', 'last_full_scan')
    op.alter_column('repository', 'completely_scanned', server_default=None)
    # ### end Alembic commands ###
