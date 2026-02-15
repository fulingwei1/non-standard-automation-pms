"""
添加售前AI成本估算模块

Revision ID: 20260215_presale_ai_cost
Create Date: 2026-02-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20260215_presale_ai_cost'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    
    # 1. 创建 AI成本估算记录表
    op.create_table(
        'presale_ai_cost_estimation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False, comment='售前工单ID'),
        sa.Column('solution_id', sa.Integer(), nullable=True, comment='解决方案ID'),
        
        # 成本分解
        sa.Column('hardware_cost', sa.DECIMAL(12, 2), nullable=True, comment='硬件成本(BOM)'),
        sa.Column('software_cost', sa.DECIMAL(12, 2), nullable=True, comment='软件成本(开发工时)'),
        sa.Column('installation_cost', sa.DECIMAL(12, 2), nullable=True, comment='安装调试成本'),
        sa.Column('service_cost', sa.DECIMAL(12, 2), nullable=True, comment='售后服务成本'),
        sa.Column('risk_reserve', sa.DECIMAL(12, 2), nullable=True, comment='风险储备金'),
        sa.Column('total_cost', sa.DECIMAL(12, 2), nullable=False, comment='总成本'),
        
        # AI分析结果
        sa.Column('optimization_suggestions', sa.JSON(), nullable=True, comment='成本优化建议'),
        sa.Column('pricing_recommendations', sa.JSON(), nullable=True, comment='定价推荐(low/medium/high)'),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=True, comment='置信度评分(0-1)'),
        
        # AI模型信息
        sa.Column('model_version', sa.String(50), nullable=True, comment='AI模型版本'),
        sa.Column('input_parameters', sa.JSON(), nullable=True, comment='输入参数快照'),
        
        # 元数据
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # 创建索引
    op.create_index('idx_presale_ticket_id', 'presale_ai_cost_estimation', ['presale_ticket_id'])
    op.create_index('idx_created_at', 'presale_ai_cost_estimation', ['created_at'])
    
    # 2. 创建 历史成本数据表
    op.create_table(
        'presale_cost_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True, comment='项目ID'),
        sa.Column('project_name', sa.String(200), nullable=True, comment='项目名称'),
        
        # 成本对比
        sa.Column('estimated_cost', sa.DECIMAL(12, 2), nullable=False, comment='估算成本'),
        sa.Column('actual_cost', sa.DECIMAL(12, 2), nullable=False, comment='实际成本'),
        sa.Column('variance_rate', sa.DECIMAL(5, 2), nullable=True, comment='偏差率(%)'),
        
        # 详细分解
        sa.Column('cost_breakdown', sa.JSON(), nullable=True, comment='成本分解详情'),
        sa.Column('variance_analysis', sa.JSON(), nullable=True, comment='偏差分析详情'),
        
        # 项目特征(用于机器学习)
        sa.Column('project_features', sa.JSON(), nullable=True, comment='项目特征向量'),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # 创建索引
    op.create_index('idx_project_id', 'presale_cost_history', ['project_id'])
    op.create_index('idx_created_at_history', 'presale_cost_history', ['created_at'])
    
    # 3. 创建 成本优化建议记录表
    op.create_table(
        'presale_cost_optimization_record',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('estimation_id', sa.Integer(), nullable=False, comment='估算记录ID'),
        
        # 优化建议
        sa.Column('optimization_type', sa.String(50), nullable=False, comment='优化类型(hardware/software/installation/service)'),
        sa.Column('original_cost', sa.DECIMAL(12, 2), nullable=False, comment='原始成本'),
        sa.Column('optimized_cost', sa.DECIMAL(12, 2), nullable=False, comment='优化后成本'),
        sa.Column('saving_amount', sa.DECIMAL(12, 2), nullable=False, comment='节省金额'),
        sa.Column('saving_rate', sa.DECIMAL(5, 2), nullable=False, comment='节省比例(%)'),
        
        # 建议详情
        sa.Column('suggestion_detail', sa.JSON(), nullable=True, comment='优化建议详情'),
        sa.Column('alternative_solutions', sa.JSON(), nullable=True, comment='替代方案'),
        
        # 可行性评估
        sa.Column('feasibility_score', sa.DECIMAL(3, 2), nullable=True, comment='可行性评分(0-1)'),
        sa.Column('risk_assessment', sa.Text(), nullable=True, comment='风险评估'),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['estimation_id'], ['presale_ai_cost_estimation.id'], name='fk_optimization_estimation'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    print("✅ AI成本估算模块数据库表创建成功")


def downgrade():
    """降级数据库"""
    op.drop_table('presale_cost_optimization_record')
    op.drop_table('presale_cost_history')
    op.drop_table('presale_ai_cost_estimation')
    print("✅ AI成本估算模块数据库表删除成功")
