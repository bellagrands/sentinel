"""Increase document column lengths

Revision ID: 85ef1d1e6dcb
Revises: 7139e94415a5
Create Date: 2025-04-07 18:05:45.475706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85ef1d1e6dcb'
down_revision = '7139e94415a5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.alter_column('document_id',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=500),
               existing_nullable=False)
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=1000),
               existing_nullable=False)
        batch_op.alter_column('content',
               existing_type=sa.TEXT(),
               nullable=True)
        batch_op.alter_column('source_type',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=100),
               existing_nullable=False)
        batch_op.alter_column('url',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.String(length=1000),
               existing_nullable=True)
        batch_op.alter_column('raw_path',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.String(length=1000),
               existing_nullable=True)
        batch_op.alter_column('processed_path',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.String(length=1000),
               existing_nullable=True)
        batch_op.drop_constraint('documents_source_type_fkey', type_='foreignkey')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.create_foreign_key('documents_source_type_fkey', 'source_configs', ['source_type'], ['source_id'])
        batch_op.alter_column('processed_path',
               existing_type=sa.String(length=1000),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
        batch_op.alter_column('raw_path',
               existing_type=sa.String(length=1000),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
        batch_op.alter_column('url',
               existing_type=sa.String(length=1000),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
        batch_op.alter_column('source_type',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
        batch_op.alter_column('content',
               existing_type=sa.TEXT(),
               nullable=False)
        batch_op.alter_column('title',
               existing_type=sa.String(length=1000),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
        batch_op.alter_column('document_id',
               existing_type=sa.String(length=500),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)

    # ### end Alembic commands ###
