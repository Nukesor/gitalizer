"""empty message

Revision ID: 47da5c15ec76
Revises: 8628f615d5dd
Create Date: 2018-05-03 22:40:44.271409

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47da5c15ec76'
down_revision = '8628f615d5dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contributor', sa.Column('location', sa.String(length=240), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('contributor', 'location')
    # ### end Alembic commands ###
