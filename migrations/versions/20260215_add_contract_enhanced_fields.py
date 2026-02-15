"""add contract enhanced fields

Revision ID: 20260215_contract_enhanced
Revises: 20260214185031_add_timesheet_reminder_tables
Create Date: 2026-02-15 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260215_contract_enhanced'
down_revision = '20260214185031_add_timesheet_reminder_tables'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    
    # 修改contracts表，添加新字段
    op.add_column('contracts', sa.Column('contract_name', sa.String(200), nullable=True, comment='合同名称'))
    op.add_column('contracts', sa.Column('contract_type', sa.String(20), nullable=True, comment='合同类型'))
    op.add_column('contracts', sa.Column('quote_id', sa.Integer(), nullable=True, comment='报价ID'))
    op.add_column('contracts', sa.Column('total_amount', sa.Numeric(15, 2), nullable=True, comment='合同总额'))
    op.add_column('contracts', sa.Column('received_amount', sa.Numeric(15, 2), server_default='0', comment='已收款'))
    op.add_column('contracts', sa.Column('unreceived_amount', sa.Numeric(15, 2), nullable=True, comment='未收款'))
    op.add_column('contracts', sa.Column('effective_date', sa.Date(), nullable=True, comment='生效日期'))
    op.add_column('contracts', sa.Column('expiry_date', sa.Date(), nullable=True, comment='到期日期'))
    op.add_column('contracts', sa.Column('contract_period', sa.Integer(), nullable=True, comment='合同期限（月）'))
    op.add_column('contracts', sa.Column('contract_subject', sa.Text(), nullable=True, comment='合同标的'))
    op.add_column('contracts', sa.Column('payment_terms', sa.Text(), nullable=True, comment='付款条件'))
    op.add_column('contracts', sa.Column('delivery_terms', sa.Text(), nullable=True, comment='交付期限'))
    op.add_column('contracts', sa.Column('sales_owner_id', sa.Integer(), nullable=True, comment='签约销售ID'))
    op.add_column('contracts', sa.Column('contract_manager_id', sa.Integer(), nullable=True, comment='合同管理员ID'))
    
    # 修改现有字段
    op.alter_column('contracts', 'contract_code', type_=sa.String(50), existing_type=sa.String(20))
    
    # 添加外键
    op.create_foreign_key('fk_contracts_quote_id', 'contracts', 'quote_versions', ['quote_id'], ['id'])
    op.create_foreign_key('fk_contracts_sales_owner', 'contracts', 'users', ['sales_owner_id'], ['id'])
    op.create_foreign_key('fk_contracts_contract_manager', 'contracts', 'users', ['contract_manager_id'], ['id'])
    
    # 添加索引
    op.create_index('idx_contract_expiry_date', 'contracts', ['expiry_date'])
    
    # 创建contract_terms表
    op.create_table(
        'contract_terms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键'),
        sa.Column('contract_id', sa.Integer(), nullable=False, comment='合同ID'),
        sa.Column('term_type', sa.String(20), nullable=False, comment='条款类型'),
        sa.Column('term_content', sa.Text(), nullable=False, comment='条款内容'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], name='fk_contract_terms_contract_id'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='合同条款表'
    )
    op.create_index('idx_contract_term_contract', 'contract_terms', ['contract_id'])
    
    # 创建contract_attachments表
    op.create_table(
        'contract_attachments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键'),
        sa.Column('contract_id', sa.Integer(), nullable=False, comment='合同ID'),
        sa.Column('file_name', sa.String(200), nullable=False, comment='文件名'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='文件路径'),
        sa.Column('file_type', sa.String(50), nullable=True, comment='文件类型'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('uploaded_by', sa.Integer(), nullable=True, comment='上传人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], name='fk_contract_attachments_contract_id'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name='fk_contract_attachments_uploaded_by'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='合同附件表'
    )
    op.create_index('idx_contract_attachment_contract', 'contract_attachments', ['contract_id'])
    
    # 修改contract_approvals表字段
    op.alter_column('contract_approvals', 'approval_result',
                    new_column_name='approval_status',
                    existing_type=sa.String(20),
                    comment='审批状态')


def downgrade():
    """降级数据库"""
    
    # 删除contract_attachments表
    op.drop_index('idx_contract_attachment_contract', 'contract_attachments')
    op.drop_table('contract_attachments')
    
    # 删除contract_terms表
    op.drop_index('idx_contract_term_contract', 'contract_terms')
    op.drop_table('contract_terms')
    
    # 删除contracts表的新字段
    op.drop_index('idx_contract_expiry_date', 'contracts')
    op.drop_constraint('fk_contracts_contract_manager', 'contracts', type_='foreignkey')
    op.drop_constraint('fk_contracts_sales_owner', 'contracts', type_='foreignkey')
    op.drop_constraint('fk_contracts_quote_id', 'contracts', type_='foreignkey')
    
    op.drop_column('contracts', 'contract_manager_id')
    op.drop_column('contracts', 'sales_owner_id')
    op.drop_column('contracts', 'delivery_terms')
    op.drop_column('contracts', 'payment_terms')
    op.drop_column('contracts', 'contract_subject')
    op.drop_column('contracts', 'contract_period')
    op.drop_column('contracts', 'expiry_date')
    op.drop_column('contracts', 'effective_date')
    op.drop_column('contracts', 'unreceived_amount')
    op.drop_column('contracts', 'received_amount')
    op.drop_column('contracts', 'total_amount')
    op.drop_column('contracts', 'quote_id')
    op.drop_column('contracts', 'contract_type')
    op.drop_column('contracts', 'contract_name')
    
    op.alter_column('contracts', 'contract_code', type_=sa.String(20), existing_type=sa.String(50))
    
    # 恢复contract_approvals表字段名
    op.alter_column('contract_approvals', 'approval_status',
                    new_column_name='approval_result',
                    existing_type=sa.String(20))
