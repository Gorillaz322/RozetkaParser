"""empty message

Revision ID: 3254b45dba30
Revises: 1dcb11c0db95
Create Date: 2016-06-30 16:30:41.231735

"""

# revision identifiers, used by Alembic.
revision = '3254b45dba30'
down_revision = '1dcb11c0db95'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('price', 'price',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('product', 'type',
               existing_type=sa.VARCHAR(length=256),
               nullable=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('product', 'type',
               existing_type=sa.VARCHAR(length=256),
               nullable=True)
    op.alter_column('price', 'price',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    ### end Alembic commands ###
