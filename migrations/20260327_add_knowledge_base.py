# -*- coding: utf-8 -*-
"""
添加知识自动沉淀模块表
迁移时间：2026-03-27
"""

from alembic import op
import sqlalchemy as sa

revision = '20260327_knowledge'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级迁移"""
    # ── knowledge_entries 知识库条目表 ──
    op.create_table(
        'knowledge_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('entry_code', sa.String(length=50), nullable=False, comment='知识编号'),
        sa.Column('knowledge_type', sa.Enum(
            'RISK_RESPONSE', 'ISSUE_SOLUTION', 'CHANGE_PATTERN',
            'DELAY_CAUSE', 'BEST_PRACTICE', 'PITFALL',
            name='knowledgetypeenum'), nullable=False, comment='知识类型'),
        sa.Column('source_type', sa.Enum(
            'RISK', 'ISSUE', 'ECN', 'LOG', 'REVIEW', 'MANUAL',
            name='knowledgesourceenum'), nullable=False, comment='来源类型'),
        sa.Column('title', sa.String(length=300), nullable=False, comment='标题'),
        sa.Column('summary', sa.Text(), nullable=False, comment='摘要'),
        sa.Column('detail', sa.Text(), nullable=True, comment='详细内容'),
        sa.Column('problem_description', sa.Text(), nullable=True, comment='问题描述'),
        sa.Column('solution', sa.Text(), nullable=True, comment='解决方案'),
        sa.Column('root_cause', sa.Text(), nullable=True, comment='根因分析'),
        sa.Column('impact', sa.Text(), nullable=True, comment='影响范围'),
        sa.Column('prevention', sa.Text(), nullable=True, comment='预防措施'),
        sa.Column('source_project_id', sa.Integer(), nullable=True, comment='来源项目ID'),
        sa.Column('source_record_id', sa.Integer(), nullable=True, comment='来源记录ID'),
        sa.Column('source_record_type', sa.String(length=30), nullable=True, comment='来源记录表名'),
        sa.Column('project_type', sa.String(length=50), nullable=True, comment='适用项目类型'),
        sa.Column('product_category', sa.String(length=50), nullable=True, comment='适用产品类别'),
        sa.Column('industry', sa.String(length=50), nullable=True, comment='适用行业'),
        sa.Column('customer_id', sa.Integer(), nullable=True, comment='关联客户ID'),
        sa.Column('applicable_stages', sa.JSON(), nullable=True, comment='适用阶段列表'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签列表'),
        sa.Column('risk_type', sa.String(length=30), nullable=True, comment='风险类型'),
        sa.Column('issue_category', sa.String(length=30), nullable=True, comment='问题分类'),
        sa.Column('change_type', sa.String(length=30), nullable=True, comment='变更类型'),
        sa.Column('view_count', sa.Integer(), default=0, comment='查看次数'),
        sa.Column('cite_count', sa.Integer(), default=0, comment='引用次数'),
        sa.Column('usefulness_score', sa.Float(), default=0.0, comment='有用性评分'),
        sa.Column('vote_count', sa.Integer(), default=0, comment='投票数'),
        sa.Column('status', sa.Enum(
            'DRAFT', 'PUBLISHED', 'ARCHIVED',
            name='knowledgestatusenum'), nullable=False, server_default='DRAFT', comment='状态'),
        sa.Column('ai_generated', sa.Boolean(), default=False, comment='是否AI自动提取'),
        sa.Column('ai_confidence', sa.Numeric(precision=5, scale=4), nullable=True, comment='AI置信度'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='审核时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['source_project_id'], ['projects.id'], name='fk_ke_source_project'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name='fk_ke_customer'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name='fk_ke_reviewed_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_ke_created_by'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_code', name='uq_ke_entry_code'),
        comment='知识库条目表',
    )

    op.create_index('idx_ke_code', 'knowledge_entries', ['entry_code'])
    op.create_index('idx_ke_type', 'knowledge_entries', ['knowledge_type'])
    op.create_index('idx_ke_source_type', 'knowledge_entries', ['source_type'])
    op.create_index('idx_ke_source_project', 'knowledge_entries', ['source_project_id'])
    op.create_index('idx_ke_project_type', 'knowledge_entries', ['project_type'])
    op.create_index('idx_ke_product_category', 'knowledge_entries', ['product_category'])
    op.create_index('idx_ke_industry', 'knowledge_entries', ['industry'])
    op.create_index('idx_ke_customer', 'knowledge_entries', ['customer_id'])
    op.create_index('idx_ke_status', 'knowledge_entries', ['status'])
    op.create_index('idx_ke_risk_type', 'knowledge_entries', ['risk_type'])
    op.create_index('idx_ke_issue_category', 'knowledge_entries', ['issue_category'])
    op.create_index('idx_ke_change_type', 'knowledge_entries', ['change_type'])

    # ── knowledge_alerts 知识预警推送记录表 ──
    op.create_table(
        'knowledge_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('target_project_id', sa.Integer(), nullable=False, comment='目标项目ID'),
        sa.Column('knowledge_entry_id', sa.Integer(), nullable=False, comment='知识条目ID'),
        sa.Column('match_reason', sa.String(length=200), nullable=True, comment='匹配原因'),
        sa.Column('match_score', sa.Float(), default=0.0, comment='匹配度评分'),
        sa.Column('is_read', sa.Boolean(), default=False, comment='是否已读'),
        sa.Column('is_adopted', sa.Boolean(), nullable=True, comment='是否采纳'),
        sa.Column('feedback', sa.Text(), nullable=True, comment='用户反馈'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['target_project_id'], ['projects.id'], name='fk_ka_target_project'),
        sa.ForeignKeyConstraint(['knowledge_entry_id'], ['knowledge_entries.id'], name='fk_ka_knowledge_entry'),
        sa.PrimaryKeyConstraint('id'),
        comment='知识预警推送记录表',
    )

    op.create_index('idx_ka_target_project', 'knowledge_alerts', ['target_project_id'])
    op.create_index('idx_ka_knowledge_entry', 'knowledge_alerts', ['knowledge_entry_id'])
    op.create_index('idx_ka_is_read', 'knowledge_alerts', ['is_read'])


def downgrade():
    """回退迁移"""
    op.drop_table('knowledge_alerts')
    op.drop_table('knowledge_entries')
