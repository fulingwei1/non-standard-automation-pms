"""add user_dashboard_layouts table

Revision ID: a3f7d8e91b2c
Revises:
Create Date: 2026-03-27
"""

from alembic import op
import sqlalchemy as sa

revision = "a3f7d8e91b2c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_dashboard_layouts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role_code", sa.String(50), nullable=False),
        sa.Column("layout_config", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_udl_user_role",
        "user_dashboard_layouts",
        ["user_id", "role_code"],
        unique=True,
    )


def downgrade():
    op.drop_index("idx_udl_user_role", table_name="user_dashboard_layouts")
    op.drop_table("user_dashboard_layouts")
