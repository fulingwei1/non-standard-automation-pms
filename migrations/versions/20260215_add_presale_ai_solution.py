"""
添加售前AI方案生成模块表

Revision ID: 20260215_ai_solution
Revises: 
Create Date: 2026-02-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '20260215_ai_solution'
down_revision = None  # 替换为实际的上一个版本ID
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    
    # 创建 presale_ai_solution 表
    op.create_table(
        'presale_ai_solution',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False, comment='售前工单ID'),
        sa.Column('requirement_analysis_id', sa.Integer(), nullable=True, comment='需求分析ID'),
        sa.Column('matched_template_ids', sa.JSON(), nullable=True, comment='匹配的模板ID列表 (TOP 3)'),
        sa.Column('generated_solution', sa.JSON(), nullable=True, comment='生成的完整方案 JSON 格式'),
        sa.Column('architecture_diagram', sa.Text(), nullable=True, comment='系统架构图 Mermaid 代码'),
        sa.Column('topology_diagram', sa.Text(), nullable=True, comment='设备拓扑图 Mermaid 代码'),
        sa.Column('signal_flow_diagram', sa.Text(), nullable=True, comment='信号流程图 Mermaid 代码'),
        sa.Column('bom_list', sa.JSON(), nullable=True, comment='BOM清单 JSON 格式'),
        sa.Column('solution_description', sa.Text(), nullable=True, comment='方案描述'),
        sa.Column('technical_parameters', sa.JSON(), nullable=True, comment='技术参数表'),
        sa.Column('process_flow', sa.Text(), nullable=True, comment='工艺流程说明'),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=True, comment='方案置信度评分 (0-1)'),
        sa.Column('quality_score', sa.DECIMAL(3, 2), nullable=True, comment='方案质量评分 (0-5)'),
        sa.Column('estimated_cost', sa.DECIMAL(12, 2), nullable=True, comment='预估成本'),
        sa.Column('cost_breakdown', sa.JSON(), nullable=True, comment='成本分解'),
        sa.Column('ai_model_used', sa.String(100), nullable=True, comment='使用的AI模型'),
        sa.Column('generation_time_seconds', sa.DECIMAL(6, 2), nullable=True, comment='生成耗时(秒)'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, comment='Prompt tokens'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, comment='Completion tokens'),
        sa.Column('status', sa.String(50), server_default='draft', nullable=True, comment='状态: draft/reviewing/approved/rejected'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='审核时间'),
        sa.Column('review_comments', sa.Text(), nullable=True, comment='审核意见'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['requirement_analysis_id'], ['presale_ai_requirement_analysis.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_presale_ticket', 'presale_ai_solution', ['presale_ticket_id'])
    op.create_index('idx_status', 'presale_ai_solution', ['status'])
    op.create_index('idx_created_at', 'presale_ai_solution', ['created_at'])
    
    # 创建 presale_solution_templates 表
    op.create_table(
        'presale_solution_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('name', sa.String(200), nullable=False, comment='模板名称'),
        sa.Column('code', sa.String(100), nullable=True, comment='模板编码'),
        sa.Column('industry', sa.String(100), nullable=True, comment='行业分类: 汽车/电子/医疗/食品等'),
        sa.Column('equipment_type', sa.String(100), nullable=True, comment='设备类型: 装配/焊接/检测/包装等'),
        sa.Column('complexity_level', sa.String(50), nullable=True, comment='复杂度: simple/medium/complex'),
        sa.Column('solution_content', sa.JSON(), nullable=True, comment='方案内容模板'),
        sa.Column('architecture_diagram', sa.Text(), nullable=True, comment='架构图模板 (Mermaid)'),
        sa.Column('bom_template', sa.JSON(), nullable=True, comment='BOM模板'),
        sa.Column('technical_specs', sa.JSON(), nullable=True, comment='技术规格参数'),
        sa.Column('equipment_list', sa.JSON(), nullable=True, comment='设备清单'),
        sa.Column('embedding', sa.Text(), nullable=True, comment='文本嵌入向量 (JSON字符串)'),
        sa.Column('embedding_model', sa.String(100), nullable=True, comment='嵌入模型名称'),
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=True, comment='使用次数'),
        sa.Column('success_rate', sa.DECIMAL(3, 2), nullable=True, comment='成功率'),
        sa.Column('avg_quality_score', sa.DECIMAL(3, 2), nullable=True, comment='平均质量评分'),
        sa.Column('typical_cost_range_min', sa.DECIMAL(12, 2), nullable=True, comment='典型成本范围-最小值'),
        sa.Column('typical_cost_range_max', sa.DECIMAL(12, 2), nullable=True, comment='典型成本范围-最大值'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签列表'),
        sa.Column('keywords', sa.Text(), nullable=True, comment='关键词 (用于全文搜索)'),
        sa.Column('is_active', sa.Integer(), server_default='1', nullable=True, comment='是否启用: 1启用/0禁用'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # 创建索引
    op.create_index('idx_industry_equipment', 'presale_solution_templates', ['industry', 'equipment_type'])
    op.create_index('idx_complexity', 'presale_solution_templates', ['complexity_level'])
    op.create_index('idx_active', 'presale_solution_templates', ['is_active'])
    op.create_index('idx_usage', 'presale_solution_templates', ['usage_count'])
    
    # 创建 presale_ai_generation_log 表
    op.create_table(
        'presale_ai_generation_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('solution_id', sa.Integer(), nullable=True, comment='方案ID'),
        sa.Column('request_type', sa.String(50), nullable=True, comment='请求类型: template_match/solution/architecture/bom'),
        sa.Column('input_data', sa.JSON(), nullable=True, comment='输入数据'),
        sa.Column('output_data', sa.JSON(), nullable=True, comment='输出数据'),
        sa.Column('success', sa.Integer(), nullable=True, comment='是否成功: 1成功/0失败'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('response_time_ms', sa.Integer(), nullable=True, comment='响应时间(毫秒)'),
        sa.Column('ai_model', sa.String(100), nullable=True, comment='AI模型'),
        sa.Column('tokens_used', sa.Integer(), nullable=True, comment='使用的token数'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['solution_id'], ['presale_ai_solution.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_solution_id', 'presale_ai_generation_log', ['solution_id'])
    op.create_index('idx_request_type', 'presale_ai_generation_log', ['request_type'])
    op.create_index('idx_log_created_at', 'presale_ai_generation_log', ['created_at'])


def downgrade():
    """降级数据库"""
    
    # 删除索引
    op.drop_index('idx_log_created_at', 'presale_ai_generation_log')
    op.drop_index('idx_request_type', 'presale_ai_generation_log')
    op.drop_index('idx_solution_id', 'presale_ai_generation_log')
    
    op.drop_index('idx_usage', 'presale_solution_templates')
    op.drop_index('idx_active', 'presale_solution_templates')
    op.drop_index('idx_complexity', 'presale_solution_templates')
    op.drop_index('idx_industry_equipment', 'presale_solution_templates')
    
    op.drop_index('idx_created_at', 'presale_ai_solution')
    op.drop_index('idx_status', 'presale_ai_solution')
    op.drop_index('idx_presale_ticket', 'presale_ai_solution')
    
    # 删除表
    op.drop_table('presale_ai_generation_log')
    op.drop_table('presale_solution_templates')
    op.drop_table('presale_ai_solution')
