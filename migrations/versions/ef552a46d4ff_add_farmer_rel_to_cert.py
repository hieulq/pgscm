"""add farmer relationship to cert

Revision ID: ef552a46d4ff
Revises: de313b629296
Create Date: 2017-07-20 10:27:26.932670

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ef552a46d4ff'
down_revision = 'de313b629296'


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('certificate', sa.Column('owner_farmer_id',
                                           sa.String(length=64),
                                           nullable=True))
    op.create_foreign_key(None, 'certificate', 'farmer',
                          ['owner_farmer_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'certificate', type_='foreignkey')
    op.drop_column('certificate', 'owner_farmer_id')
    # ### end Alembic commands ###
