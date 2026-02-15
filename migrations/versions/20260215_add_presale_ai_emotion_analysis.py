"""
添加AI客户情绪分析相关表

Revision ID: 20260215_ai_emotion
Create Date: 2026-02-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers
revision = '20260215_ai_emotion'
down_revision = '20260215_sales_team_management'
branch_labels = None
depends_on = None


def upgrade():
    # 创建客户情绪分析记录表
    op.create_table(
        'presale_ai_emotion_analysis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False, comment='售前工单ID'),
        sa.Column('customer_id', sa.Integer(), nullable=False, comment='客户ID'),
        sa.Column('communication_content', sa.Text(), nullable=True, comment='沟通内容'),
        sa.Column('sentiment', sa.Enum('positive', 'neutral', 'negative', name='sentimenttype'), nullable=True, comment='情绪类型'),
        sa.Column('purchase_intent_score', sa.DECIMAL(5, 2), nullable=True, comment='购买意向评分(0-100)'),
        sa.Column('churn_risk', sa.Enum('high', 'medium', 'low', name='churnrisklevel'), nullable=True, comment='流失风险等级'),
        sa.Column('emotion_factors', sa.JSON(), nullable=True, comment='影响情绪的因素'),
        sa.Column('analysis_result', sa.Text(), nullable=True, comment='分析结果详情'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['presale_ticket_id'], ['presale_tickets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='AI客户情绪分析记录表'
    )
    
    # 创建索引
    op.create_index('idx_presale_ticket_id', 'presale_ai_emotion_analysis', ['presale_ticket_id'])
    op.create_index('idx_customer_id', 'presale_ai_emotion_analysis', ['customer_id'])
    
    # 创建跟进提醒表
    op.create_table(
        'presale_follow_up_reminder',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False, comment='售前工单ID'),
        sa.Column('recommended_time', sa.DateTime(), nullable=True, comment='推荐跟进时间'),
        sa.Column('priority', sa.Enum('high', 'medium', 'low', name='reminderpriority'), nullable=True, comment='优先级'),
        sa.Column('follow_up_content', sa.Text(), nullable=True, comment='跟进内容建议'),
        sa.Column('reason', sa.Text(), nullable=True, comment='最佳时机理由'),
        sa.Column('status', sa.Enum('pending', 'completed', 'dismissed', name='reminderstatus'), server_default='pending', nullable=True, comment='状态'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['presale_ticket_id'], ['presale_tickets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='跟进提醒表'
    )
    
    # 创建索引
    op.create_index('idx_reminder_presale_ticket_id', 'presale_follow_up_reminder', ['presale_ticket_id'])
    op.create_index('idx_reminder_status', 'presale_follow_up_reminder', ['status'])
    op.create_index('idx_reminder_priority', 'presale_follow_up_reminder', ['priority'])
    
    # 创建情绪趋势表
    op.create_table(
        'presale_emotion_trend',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False, comment='售前工单ID'),
        sa.Column('customer_id', sa.Integer(), nullable=False, comment='客户ID'),
        sa.Column('trend_data', sa.JSON(), nullable=True, comment='趋势数据 [{date, sentiment, intent_score}]'),
        sa.Column('key_turning_points', sa.JSON(), nullable=True, comment='关键转折点'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['presale_ticket_id'], ['presale_tickets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='情绪趋势表'
    )
    
    # 创建索引
    op.create_index('idx_trend_presale_ticket_id', 'presale_emotion_trend', ['presale_ticket_id'])
    op.create_index('idx_trend_customer_id', 'presale_emotion_trend', ['customer_id'])


def downgrade():
    # 删除表
    op.drop_table('presale_emotion_trend')
    op.drop_table('presale_follow_up_reminder')
    op.drop_table('presale_ai_emotion_analysis')
    
    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS sentimenttype")
    op.execute("DROP TYPE IF EXISTS churnrisklevel")
    op.execute("DROP TYPE IF EXISTS reminderpriority")
    op.execute("DROP TYPE IF EXISTS reminderstatus")
