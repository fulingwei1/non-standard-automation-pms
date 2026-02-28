"""
添加AI报价单自动生成相关表
Team 5: AI Quotation Generator Tables

创建时间: 2026-02-15
版本: 20260215_add_presale_ai_quotation
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260215_add_presale_ai_quotation'
down_revision = None  # 根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    
    # 创建presale_ai_quotation表
    op.create_table(
        'presale_ai_quotation',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='主键ID'),
        sa.Column('presale_ticket_id', sa.Integer(), nullable=False, comment='售前工单ID'),
        sa.Column('customer_id', sa.Integer(), nullable=True, comment='客户ID'),
        sa.Column('quotation_number', sa.String(50), nullable=False, unique=True, comment='报价单编号'),
        sa.Column('quotation_type', sa.Enum('basic', 'standard', 'premium', name='quotation_type'), 
                  nullable=False, comment='报价单类型'),
        sa.Column('items', sa.JSON(), nullable=False, comment='报价项清单'),
        sa.Column('subtotal', sa.DECIMAL(12, 2), nullable=False, comment='小计'),
        sa.Column('tax', sa.DECIMAL(12, 2), nullable=False, server_default='0', comment='税费'),
        sa.Column('discount', sa.DECIMAL(12, 2), nullable=False, server_default='0', comment='折扣'),
        sa.Column('total', sa.DECIMAL(12, 2), nullable=False, comment='总计'),
        sa.Column('payment_terms', sa.Text(), nullable=True, comment='付款条款'),
        sa.Column('validity_days', sa.Integer(), nullable=False, server_default='30', comment='有效期（天）'),
        sa.Column('status', sa.Enum('draft', 'pending_approval', 'approved', 'sent', 'accepted', 'rejected', 
                                    name='quotation_status'), 
                  nullable=False, server_default='draft', comment='状态'),
        sa.Column('pdf_url', sa.String(255), nullable=True, comment='PDF文件URL'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='版本号'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('ai_prompt', sa.Text(), nullable=True, comment='AI生成时使用的提示词'),
        sa.Column('ai_model', sa.String(50), nullable=True, comment='使用的AI模型'),
        sa.Column('generation_time', sa.DECIMAL(5, 2), nullable=True, comment='生成耗时（秒）'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quotation_number'),
        comment='AI报价单生成记录表'
    )
    
    # 创建索引
    op.create_index('idx_presale_ticket_id', 'presale_ai_quotation', ['presale_ticket_id'])
    op.create_index('idx_customer_id', 'presale_ai_quotation', ['customer_id'])
    op.create_index('idx_status', 'presale_ai_quotation', ['status'])
    op.create_index('idx_created_at', 'presale_ai_quotation', ['created_at'])
    
    # 创建quotation_templates表
    op.create_table(
        'quotation_templates',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='主键ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='模板名称'),
        sa.Column('template_type', sa.Enum('basic', 'standard', 'premium', name='template_type'), 
                  nullable=False, comment='模板类型'),
        sa.Column('template_content', sa.JSON(), nullable=False, comment='模板内容'),
        sa.Column('pdf_template_path', sa.String(255), nullable=True, comment='PDF模板路径'),
        sa.Column('default_validity_days', sa.Integer(), nullable=False, server_default='30', comment='默认有效期'),
        sa.Column('default_tax_rate', sa.DECIMAL(5, 4), nullable=False, server_default='0.1300', comment='默认税率'),
        sa.Column('default_discount_rate', sa.DECIMAL(5, 4), nullable=False, server_default='0.0000', comment='默认折扣率'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否启用'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.PrimaryKeyConstraint('id'),
        comment='报价单模板库'
    )
    
    # 创建索引
    op.create_index('idx_template_type', 'quotation_templates', ['template_type'])
    op.create_index('idx_is_active', 'quotation_templates', ['is_active'])
    
    # 创建quotation_approvals表
    op.create_table(
        'quotation_approvals',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='主键ID'),
        sa.Column('quotation_id', sa.Integer(), nullable=False, comment='报价单ID'),
        sa.Column('approver_id', sa.Integer(), nullable=False, comment='审批人ID'),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='approval_status'), 
                  nullable=False, server_default='pending', comment='审批状态'),
        sa.Column('comments', sa.Text(), nullable=True, comment='审批意见'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('approved_at', sa.TIMESTAMP(), nullable=True, comment='审批时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['quotation_id'], ['presale_ai_quotation.id'], ondelete='CASCADE'),
        comment='报价单审批记录'
    )
    
    # 创建索引
    op.create_index('idx_quotation_id_approval', 'quotation_approvals', ['quotation_id'])
    op.create_index('idx_approver_id', 'quotation_approvals', ['approver_id'])
    op.create_index('idx_approval_status', 'quotation_approvals', ['status'])
    
    # 创建quotation_versions表
    op.create_table(
        'quotation_versions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='主键ID'),
        sa.Column('quotation_id', sa.Integer(), nullable=False, comment='报价单ID'),
        sa.Column('version', sa.Integer(), nullable=False, comment='版本号'),
        sa.Column('snapshot_data', sa.JSON(), nullable=False, comment='版本快照数据'),
        sa.Column('changed_by', sa.Integer(), nullable=False, comment='变更人ID'),
        sa.Column('change_summary', sa.Text(), nullable=True, comment='变更摘要'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['quotation_id'], ['presale_ai_quotation.id'], ondelete='CASCADE'),
        comment='报价单版本历史'
    )
    
    # 创建索引
    op.create_index('idx_quotation_id_version', 'quotation_versions', ['quotation_id'])
    op.create_index('idx_version', 'quotation_versions', ['version'])
    op.create_index('idx_created_at_version', 'quotation_versions', ['created_at'])


def downgrade():
    """降级数据库"""
    
    # 删除索引和表（按相反顺序）
    op.drop_index('idx_created_at_version', 'quotation_versions')
    op.drop_index('idx_version', 'quotation_versions')
    op.drop_index('idx_quotation_id_version', 'quotation_versions')
    op.drop_table('quotation_versions')
    
    op.drop_index('idx_approval_status', 'quotation_approvals')
    op.drop_index('idx_approver_id', 'quotation_approvals')
    op.drop_index('idx_quotation_id_approval', 'quotation_approvals')
    op.drop_table('quotation_approvals')
    
    op.drop_index('idx_is_active', 'quotation_templates')
    op.drop_index('idx_template_type', 'quotation_templates')
    op.drop_table('quotation_templates')
    
    op.drop_index('idx_created_at', 'presale_ai_quotation')
    op.drop_index('idx_status', 'presale_ai_quotation')
    op.drop_index('idx_customer_id', 'presale_ai_quotation')
    op.drop_index('idx_presale_ticket_id', 'presale_ai_quotation')
    op.drop_table('presale_ai_quotation')
    
    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS quotation_type")
    op.execute("DROP TYPE IF EXISTS quotation_status")
    op.execute("DROP TYPE IF EXISTS template_type")
    op.execute("DROP TYPE IF EXISTS approval_status")
