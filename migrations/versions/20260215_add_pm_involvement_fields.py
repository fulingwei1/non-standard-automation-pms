"""add pm involvement fields to presale tickets

Revision ID: 20260215_pm_involvement
Revises: 
Create Date: 2026-02-15 13:46:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260215_pm_involvement'
down_revision = None  # 设置为上一个迁移的ID
branch_labels = None
depends_on = None


def upgrade():
    """添加PM介入相关字段"""
    # 添加PM介入相关字段到 presale_support_ticket 表
    op.add_column('presale_support_ticket', 
        sa.Column('pm_involvement_required', sa.Boolean(), default=False, comment='是否需要PM提前介入'))
    op.add_column('presale_support_ticket', 
        sa.Column('pm_involvement_risk_level', sa.String(20), comment='风险等级（高/低）'))
    op.add_column('presale_support_ticket', 
        sa.Column('pm_involvement_risk_factors', sa.JSON(), comment='风险因素列表'))
    op.add_column('presale_support_ticket', 
        sa.Column('pm_involvement_checked_at', sa.DateTime(), comment='PM介入检查时间'))
    op.add_column('presale_support_ticket', 
        sa.Column('pm_assigned', sa.Boolean(), default=False, comment='PM是否已分配'))
    op.add_column('presale_support_ticket', 
        sa.Column('pm_user_id', sa.Integer(), comment='分配的PM用户ID'))
    op.add_column('presale_support_ticket', 
        sa.Column('pm_assigned_at', sa.DateTime(), comment='PM分配时间'))
    
    # 添加外键约束
    try:
        op.create_foreign_key(
            'fk_presale_ticket_pm_user', 
            'presale_support_ticket', 
            'users', 
            ['pm_user_id'], 
            ['id']
        )
    except Exception:
        # 如果外键已存在，忽略错误
        pass
    
    # 添加索引
    try:
        op.create_index('idx_pm_involvement_required', 'presale_support_ticket', ['pm_involvement_required'])
        op.create_index('idx_pm_assigned', 'presale_support_ticket', ['pm_assigned'])
    except Exception:
        pass


def downgrade():
    """回滚PM介入相关字段"""
    # 删除索引
    try:
        op.drop_index('idx_pm_assigned', 'presale_support_ticket')
        op.drop_index('idx_pm_involvement_required', 'presale_support_ticket')
    except Exception:
        pass
    
    # 删除外键
    try:
        op.drop_constraint('fk_presale_ticket_pm_user', 'presale_support_ticket', type_='foreignkey')
    except Exception:
        pass
    
    # 删除列
    op.drop_column('presale_support_ticket', 'pm_assigned_at')
    op.drop_column('presale_support_ticket', 'pm_user_id')
    op.drop_column('presale_support_ticket', 'pm_assigned')
    op.drop_column('presale_support_ticket', 'pm_involvement_checked_at')
    op.drop_column('presale_support_ticket', 'pm_involvement_risk_factors')
    op.drop_column('presale_support_ticket', 'pm_involvement_risk_level')
    op.drop_column('presale_support_ticket', 'pm_involvement_required')
