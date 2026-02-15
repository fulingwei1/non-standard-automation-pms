"""Team 10: AI Integration Tables - AI使用统计和反馈表

Revision ID: team10_ai_integration
Revises: 
Create Date: 2026-02-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'team10_ai_integration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # AI功能使用统计表
    op.create_table(
        'presale_ai_usage_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ai_function', 
                  sa.Enum('requirement', 'solution', 'cost', 'winrate', 'quotation', 
                         'knowledge', 'script', 'emotion', 'mobile', name='ai_function_enum'),
                  nullable=False),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('success_count', sa.Integer(), default=0),
        sa.Column('avg_response_time', sa.Integer(), comment='平均响应时间(毫秒)'),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_user_function_date', 'user_id', 'ai_function', 'date'),
        sa.Index('idx_date', 'date'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # AI反馈表
    op.create_table(
        'presale_ai_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ai_function', sa.String(50), nullable=False),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False, comment='评分1-5星'),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_user_function', 'user_id', 'ai_function'),
        sa.Index('idx_rating', 'rating'),
        sa.Index('idx_created_at', 'created_at'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # AI配置表
    op.create_table(
        'presale_ai_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ai_function', sa.String(50), nullable=False, unique=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('temperature', sa.Float(), default=0.7),
        sa.Column('max_tokens', sa.Integer(), default=2000),
        sa.Column('timeout_seconds', sa.Integer(), default=30),
        sa.Column('config_json', sa.JSON(), nullable=True, comment='其他配置参数'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # AI工作流日志表
    op.create_table(
        'presale_ai_workflow_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False),
        sa.Column('workflow_step', 
                  sa.Enum('requirement', 'solution', 'cost', 'winrate', 'quotation', name='workflow_step_enum'),
                  nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'success', 'failed', name='workflow_status_enum'), 
                  default='pending'),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_ticket_step', 'presale_ticket_id', 'workflow_step'),
        sa.Index('idx_status', 'status'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # AI审计日志表
    op.create_table(
        'presale_ai_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False, comment='操作类型'),
        sa.Column('ai_function', sa.String(50), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_user_action', 'user_id', 'action'),
        sa.Index('idx_created_at', 'created_at'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade():
    op.drop_table('presale_ai_audit_log')
    op.drop_table('presale_ai_workflow_log')
    op.drop_table('presale_ai_config')
    op.drop_table('presale_ai_feedback')
    op.drop_table('presale_ai_usage_stats')
