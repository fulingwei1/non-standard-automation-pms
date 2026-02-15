"""
添加AI需求理解记录表

Revision ID: 20260215_ai_requirement
Revises: 20260215_sales_team_management
Create Date: 2026-02-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '20260215_ai_requirement'
down_revision = '20260215_sales_team_management'
branch_labels = None
depends_on = None


def upgrade():
    """创建presale_ai_requirement_analysis表"""
    
    op.create_table(
        'presale_ai_requirement_analysis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False),
        sa.Column('raw_requirement', sa.Text(), nullable=False, comment='客户原始需求描述'),
        sa.Column('structured_requirement', sa.JSON(), nullable=True, comment='结构化需求数据'),
        sa.Column('clarification_questions', sa.JSON(), nullable=True, comment='澄清问题列表'),
        sa.Column('confidence_score', sa.DECIMAL(precision=3, scale=2), nullable=True, comment='需求理解置信度 0.00-1.00'),
        sa.Column('feasibility_analysis', sa.JSON(), nullable=True, comment='技术可行性分析'),
        sa.Column('equipment_list', sa.JSON(), nullable=True, comment='识别的设备清单'),
        sa.Column('process_flow', sa.JSON(), nullable=True, comment='工艺流程数据'),
        sa.Column('technical_parameters', sa.JSON(), nullable=True, comment='技术参数规格'),
        sa.Column('acceptance_criteria', sa.JSON(), nullable=True, comment='验收标准建议'),
        sa.Column('ai_model_used', sa.String(length=100), nullable=True, comment='使用的AI模型'),
        sa.Column('ai_analysis_version', sa.String(length=50), nullable=True, comment='分析算法版本'),
        sa.Column('status', sa.String(length=50), server_default='draft', nullable=True, comment='状态: draft/reviewed/approved/rejected'),
        sa.Column('is_refined', sa.Boolean(), server_default='0', nullable=True, comment='是否已精炼'),
        sa.Column('refinement_count', sa.Integer(), server_default='0', nullable=True, comment='精炼次数'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['presale_ticket_id'], ['presale_tickets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_presale_ai_ticket_id', 'presale_ai_requirement_analysis', ['presale_ticket_id'])
    op.create_index('idx_presale_ai_status', 'presale_ai_requirement_analysis', ['status'])
    op.create_index('idx_presale_ai_confidence', 'presale_ai_requirement_analysis', ['confidence_score'])
    op.create_index('idx_presale_ai_created_at', 'presale_ai_requirement_analysis', ['created_at'])


def downgrade():
    """删除presale_ai_requirement_analysis表"""
    
    op.drop_index('idx_presale_ai_created_at', table_name='presale_ai_requirement_analysis')
    op.drop_index('idx_presale_ai_confidence', table_name='presale_ai_requirement_analysis')
    op.drop_index('idx_presale_ai_status', table_name='presale_ai_requirement_analysis')
    op.drop_index('idx_presale_ai_ticket_id', table_name='presale_ai_requirement_analysis')
    op.drop_table('presale_ai_requirement_analysis')
