"""add new column member_count to cert table

Revision ID: de313b629296
Revises: 32c1cbb13ec2
Create Date: 2017-07-20 08:55:47.250651

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'de313b629296'
down_revision = '32c1cbb13ec2'


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('certificate', sa.Column('member_count', sa.Integer(),
                                           nullable=False))
    op.alter_column('certificate', 'certificate_start_date',
               existing_type=mysql.DATETIME(),
               nullable=False)
    op.alter_column('certificate', 'gov_certificate_id',
               existing_type=mysql.VARCHAR(length=64),
               nullable=False)
    op.alter_column('certificate', 'group_area',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.alter_column('farmer', 'gender',
               existing_type=mysql.ENUM('male', 'female'),
               nullable=False)
    op.alter_column('farmer', 'name',
               existing_type=mysql.VARCHAR(length=80),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('farmer', 'name',
               existing_type=mysql.VARCHAR(length=80),
               nullable=True)
    op.alter_column('farmer', 'gender',
               existing_type=mysql.ENUM('male', 'female'),
               nullable=True)
    op.alter_column('certificate', 'group_area',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    op.alter_column('certificate', 'gov_certificate_id',
               existing_type=mysql.VARCHAR(length=64),
               nullable=True)
    op.alter_column('certificate', 'certificate_start_date',
               existing_type=mysql.DATETIME(),
               nullable=True)
    op.drop_column('certificate', 'member_count')
    # ### end Alembic commands ###
