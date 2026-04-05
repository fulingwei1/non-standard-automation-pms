"""Add version management fields to role_templates

Revision ID: role_template_version_v1
Revises:
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'role_template_version_v1'
down_revision = None  # 根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('role_templates', sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='版本号'))
    op.add_column('role_templates', sa.Column('version_note', sa.String(200), nullable=True, comment='版本说明'))
    op.add_column('role_templates', sa.Column('source_role_id', sa.Integer(), nullable=True, comment='来源角色ID'))
    op.add_column('role_templates', sa.Column('source_role_name', sa.String(100), nullable=True, comment='来源角色名称'))


def downgrade():
    op.drop_column('role_templates', 'source_role_name')
    op.drop_column('role_templates', 'source_role_id')
    op.drop_column('role_templates', 'version_note')
    op.drop_column('role_templates', 'version')
