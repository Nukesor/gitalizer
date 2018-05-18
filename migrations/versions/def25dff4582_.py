"""empty message

Revision ID: def25dff4582
Revises: 47da5c15ec76
Create Date: 2018-05-18 13:20:38.220942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'def25dff4582'
down_revision = '47da5c15ec76'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('analysis_result', sa.Column('timezone_switches', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('analysis_result', 'timezone_switches')
    # ### end Alembic commands ###
