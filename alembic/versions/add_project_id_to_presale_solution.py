"""Add project_id to presale_solution table

为 presale_solution 表添加 project_id 字段，使投标方案直接关联项目。
业务背景：一个项目可能有多个投标方案，投标方案应该直接挂在项目下面。

Revision ID: presale_solution_project_id
Revises: timesheet_analytics_v1
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'presale_solution_project_id'
down_revision = 'timesheet_analytics_v1'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 project_id 字段到 presale_solution 表
    op.add_column(
        'presale_solution',
        sa.Column('project_id', sa.Integer(), comment='关联项目ID')
    )

    # 添加外键约束
    op.create_foreign_key(
        'fk_presale_solution_project_id',
        'presale_solution',
        'projects',
        ['project_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 添加索引以加速查询
    op.create_index(
        'idx_solution_project',
        'presale_solution',
        ['project_id']
    )


def downgrade():
    # 删除索引
    op.drop_index('idx_solution_project', table_name='presale_solution')

    # 删除外键约束
    op.drop_constraint('fk_presale_solution_project_id', 'presale_solution', type_='foreignkey')

    # 删除字段
    op.drop_column('presale_solution', 'project_id')
