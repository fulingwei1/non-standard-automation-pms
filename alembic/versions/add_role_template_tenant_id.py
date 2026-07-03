"""Add tenant scope to role_templates

Revision ID: role_template_tenant_v1
Revises: role_template_version_v1
Create Date: 2026-06-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "role_template_tenant_v1"
down_revision = "role_template_version_v1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "role_templates",
        sa.Column("tenant_id", sa.Integer(), nullable=True, comment="租户ID"),
    )


def downgrade():
    op.drop_column("role_templates", "tenant_id")
