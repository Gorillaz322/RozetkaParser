"""empty message

Revision ID: 1bf81939a248
Revises: fc2c48999cb2
Create Date: 2016-07-01 18:53:52.441316

"""

# revision identifiers, used by Alembic.
revision = '1bf81939a248'
down_revision = 'fc2c48999cb2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product', sa.Column('img', sa.String(length=256), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product', 'img')
    ### end Alembic commands ###
