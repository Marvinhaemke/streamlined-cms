"""Initial database

Revision ID: 8b43c53b149c
Revises: 
Create Date: 2025-03-01 16:35:08.323052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b43c53b149c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('websites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('domain', sa.String(length=100), nullable=False),
    sa.Column('directory', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('directory'),
    sa.UniqueConstraint('domain')
    )
    op.create_table('pages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('website_id', sa.Integer(), nullable=False),
    sa.Column('path', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['website_id'], ['websites.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('website_id', 'path', name='uix_website_path')
    )
    op.create_table('content_versions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('content_json', sa.Text(), nullable=True),
    sa.Column('content_html', sa.Text(), nullable=True),
    sa.Column('version_type', sa.String(length=20), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('page_views',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=False),
    sa.Column('visitor_id', sa.String(length=64), nullable=False),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('referrer', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('split_tests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('test_type', sa.String(length=20), nullable=False),
    sa.Column('goal_page_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['goal_page_id'], ['pages.id'], ),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('test_variants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('test_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('content_version_id', sa.Integer(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['content_version_id'], ['content_versions.id'], ),
    sa.ForeignKeyConstraint(['test_id'], ['split_tests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('conversions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('split_test_id', sa.Integer(), nullable=False),
    sa.Column('variant_id', sa.Integer(), nullable=False),
    sa.Column('visitor_id', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['split_test_id'], ['split_tests.id'], ),
    sa.ForeignKeyConstraint(['variant_id'], ['test_variants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('visitor_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('split_test_id', sa.Integer(), nullable=False),
    sa.Column('variant_id', sa.Integer(), nullable=False),
    sa.Column('visitor_id', sa.String(length=64), nullable=False),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('referrer', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['split_test_id'], ['split_tests.id'], ),
    sa.ForeignKeyConstraint(['variant_id'], ['test_variants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('visitor_sessions')
    op.drop_table('conversions')
    op.drop_table('test_variants')
    op.drop_table('split_tests')
    op.drop_table('page_views')
    op.drop_table('content_versions')
    op.drop_table('pages')
    op.drop_table('websites')
    op.drop_table('users')
    # ### end Alembic commands ###
