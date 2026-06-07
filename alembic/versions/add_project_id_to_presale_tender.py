"""Add project_id to presale_tender_record table

Revision ID: presale_tender_project_id
Revises: presale_solution_project_id
Create Date: 2026-06-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "presale_tender_project_id"
down_revision = "presale_solution_project_id"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "presale_tender_record",
        sa.Column("project_id", sa.Integer(), comment="关联项目ID"),
    )
    op.create_foreign_key(
        "fk_presale_tender_record_project_id",
        "presale_tender_record",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_tender_project",
        "presale_tender_record",
        ["project_id"],
    )


def downgrade():
    op.drop_index("idx_tender_project", table_name="presale_tender_record")
    op.drop_constraint(
        "fk_presale_tender_record_project_id",
        "presale_tender_record",
        type_="foreignkey",
    )
    op.drop_column("presale_tender_record", "project_id")
