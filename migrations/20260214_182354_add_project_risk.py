# -*- coding: utf-8 -*-
"""
添加项目风险管理表
迁移时间：2026-02-14 18:23:54
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260214_182354'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级迁移"""
    op.create_table(
        'project_risks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('risk_code', sa.String(length=50), nullable=False, comment='风险编号'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('risk_name', sa.String(length=200), nullable=False, comment='风险名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='风险描述'),
        sa.Column('risk_type', sa.Enum('TECHNICAL', 'COST', 'SCHEDULE', 'QUALITY', name='risktypeenum'), nullable=False, comment='风险类型：TECHNICAL/COST/SCHEDULE/QUALITY'),
        sa.Column('probability', sa.Integer(), nullable=False, comment='发生概率（1-5）：1=很低，5=很高'),
        sa.Column('impact', sa.Integer(), nullable=False, comment='影响程度（1-5）：1=很低，5=很高'),
        sa.Column('risk_score', sa.Integer(), nullable=False, comment='风险评分（probability × impact）'),
        sa.Column('risk_level', sa.String(length=20), nullable=True, comment='风险等级：LOW/MEDIUM/HIGH/CRITICAL'),
        sa.Column('mitigation_plan', sa.Text(), nullable=True, comment='应对措施'),
        sa.Column('contingency_plan', sa.Text(), nullable=True, comment='应急计划'),
        sa.Column('owner_id', sa.Integer(), nullable=True, comment='负责人ID'),
        sa.Column('owner_name', sa.String(length=50), nullable=True, comment='负责人姓名'),
        sa.Column('status', sa.Enum('IDENTIFIED', 'ANALYZING', 'PLANNING', 'MONITORING', 'MITIGATED', 'OCCURRED', 'CLOSED', name='riskstatusenum'), nullable=False, comment='风险状态'),
        sa.Column('identified_date', sa.DateTime(), nullable=True, comment='识别日期'),
        sa.Column('target_closure_date', sa.DateTime(), nullable=True, comment='计划关闭日期'),
        sa.Column('actual_closure_date', sa.DateTime(), nullable=True, comment='实际关闭日期'),
        sa.Column('is_occurred', sa.Boolean(), nullable=True, comment='是否已发生'),
        sa.Column('occurrence_date', sa.DateTime(), nullable=True, comment='发生日期'),
        sa.Column('actual_impact', sa.Text(), nullable=True, comment='实际影响描述'),
        sa.Column('created_by_id', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('created_by_name', sa.String(length=50), nullable=True, comment='创建人姓名'),
        sa.Column('updated_by_id', sa.Integer(), nullable=True, comment='最后更新人ID'),
        sa.Column('updated_by_name', sa.String(length=50), nullable=True, comment='最后更新人姓名'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='fk_project_risks_project_id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_project_risks_owner_id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name='fk_project_risks_created_by_id'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], name='fk_project_risks_updated_by_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('risk_code', name='uq_project_risks_risk_code'),
        comment='项目风险表'
    )
    
    # 创建索引
    op.create_index('idx_project_risk_code', 'project_risks', ['risk_code'])
    op.create_index('idx_project_risk_project_id', 'project_risks', ['project_id'])
    op.create_index('idx_project_risk_type', 'project_risks', ['risk_type'])
    op.create_index('idx_project_risk_status', 'project_risks', ['status'])
    op.create_index('idx_project_risk_level', 'project_risks', ['risk_level'])
    op.create_index('idx_project_risk_owner', 'project_risks', ['owner_id'])


def downgrade():
    """降级迁移"""
    op.drop_index('idx_project_risk_owner', table_name='project_risks')
    op.drop_index('idx_project_risk_level', table_name='project_risks')
    op.drop_index('idx_project_risk_status', table_name='project_risks')
    op.drop_index('idx_project_risk_type', table_name='project_risks')
    op.drop_index('idx_project_risk_project_id', table_name='project_risks')
    op.drop_index('idx_project_risk_code', table_name='project_risks')
    op.drop_table('project_risks')
