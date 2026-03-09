# -*- coding: utf-8 -*-
"""
添加客户关系成熟度相关表和字段

包含：
1. 扩展 contacts 表，添加决策链相关字段
2. 创建 customer_relationship_scores 表

Revision ID: 20260308_relationship
Revises:
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '20260308_relationship'
down_revision = None  # 根据实际情况调整
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""

    # 1. 扩展 contacts 表，添加决策链相关字段
    # 检查列是否存在，如果不存在则添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('contacts')]

    if 'decision_role' not in columns:
        op.add_column('contacts', sa.Column(
            'decision_role',
            sa.String(20),
            comment='决策角色: EB/TB/PB/UB/COACH'
        ))

    if 'influence_level' not in columns:
        op.add_column('contacts', sa.Column(
            'influence_level',
            sa.String(10),
            comment='影响力: HIGH/MEDIUM/LOW'
        ))

    if 'attitude' not in columns:
        op.add_column('contacts', sa.Column(
            'attitude',
            sa.String(20),
            server_default='unknown',
            comment='态度: supportive/neutral/resistant/unknown'
        ))

    if 'relationship_strength' not in columns:
        op.add_column('contacts', sa.Column(
            'relationship_strength',
            sa.Integer,
            server_default='0',
            comment='关系强度 0-100'
        ))

    if 'last_contact_date' not in columns:
        op.add_column('contacts', sa.Column(
            'last_contact_date',
            sa.Date,
            comment='最后联系日期'
        ))

    if 'key_concerns' not in columns:
        op.add_column('contacts', sa.Column(
            'key_concerns',
            sa.Text,
            comment='关键关注点JSON数组'
        ))

    # 添加索引
    try:
        op.create_index('idx_contact_decision_role', 'contacts', ['decision_role'])
    except Exception:
        pass  # 索引可能已存在

    try:
        op.create_index('idx_contact_influence', 'contacts', ['influence_level'])
    except Exception:
        pass

    try:
        op.create_index('idx_contact_attitude', 'contacts', ['attitude'])
    except Exception:
        pass

    # 2. 创建 customer_relationship_scores 表
    if not inspector.has_table('customer_relationship_scores'):
        op.create_table(
            'customer_relationship_scores',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('customer_id', sa.Integer, sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, comment='客户ID'),
            sa.Column('opportunity_id', sa.Integer, sa.ForeignKey('opportunities.id', ondelete='SET NULL'), comment='关联商机'),

            # 评分日期
            sa.Column('score_date', sa.Date, nullable=False, comment='评分日期'),

            # 六维度得分
            sa.Column('decision_chain_score', sa.Integer, server_default='0', comment='决策链覆盖度 (0-20)'),
            sa.Column('interaction_frequency_score', sa.Integer, server_default='0', comment='互动频率 (0-15)'),
            sa.Column('relationship_depth_score', sa.Integer, server_default='0', comment='关系深度 (0-20)'),
            sa.Column('information_access_score', sa.Integer, server_default='0', comment='信息获取度 (0-15)'),
            sa.Column('support_level_score', sa.Integer, server_default='0', comment='支持度 (0-20)'),
            sa.Column('executive_engagement_score', sa.Integer, server_default='0', comment='高层互动 (0-10)'),

            # 汇总
            sa.Column('total_score', sa.Integer, server_default='0', comment='总分 (0-100)'),
            sa.Column('maturity_level', sa.String(5), comment='成熟度等级: L1-L5'),
            sa.Column('estimated_win_rate', sa.Integer, comment='预估赢单率 %'),

            # 评分详情
            sa.Column('score_details', sa.Text, comment='各维度评分详情JSON'),

            # 评分人
            sa.Column('scored_by', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL')),
            sa.Column('is_auto_calculated', sa.Boolean, server_default='1', comment='是否自动计算'),

            # 时间戳
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

        # 创建索引
        op.create_index('idx_rel_score_customer', 'customer_relationship_scores', ['customer_id'])
        op.create_index('idx_rel_score_date', 'customer_relationship_scores', ['score_date'])
        op.create_index('idx_rel_score_level', 'customer_relationship_scores', ['maturity_level'])
        op.create_index('idx_rel_score_opportunity', 'customer_relationship_scores', ['opportunity_id'])


def downgrade():
    """降级数据库"""

    # 删除 customer_relationship_scores 表
    op.drop_table('customer_relationship_scores')

    # 删除 contacts 表的新字段
    op.drop_column('contacts', 'key_concerns')
    op.drop_column('contacts', 'last_contact_date')
    op.drop_column('contacts', 'relationship_strength')
    op.drop_column('contacts', 'attitude')
    op.drop_column('contacts', 'influence_level')
    op.drop_column('contacts', 'decision_role')
