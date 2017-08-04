"""remove unique=True in fullname

Revision ID: 2159f60b94ab
Revises: 5c3ebec69cdd
Create Date: 2017-08-03 21:47:27.079663

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '2159f60b94ab'
down_revision = '5c3ebec69cdd'


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_user_fullname', table_name='user')
    op.create_index(op.f('ix_user_fullname'), 'user',
                    ['fullname'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_fullname'), table_name='user')
    op.create_index('ix_user_fullname', 'user', ['fullname'], unique=True)
    # ### end Alembic commands ###
