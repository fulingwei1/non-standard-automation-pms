# -*- coding: utf-8 -*-
"""
添加智能采购管理系统表

Tables:
- purchase_suggestions (采购建议)
- supplier_quotations (供应商报价)
- supplier_performances (供应商绩效)
- purchase_order_trackings (订单跟踪)

Created: 2026-02-16
Author: Team 1 - 智能采购管理系统
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """创建表"""
    
    # 1. 采购建议表
    op.create_table(
        'purchase_suggestions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('suggestion_no', sa.String(50), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('material_code', sa.String(50), nullable=False),
        sa.Column('material_name', sa.String(200), nullable=False),
        sa.Column('specification', sa.String(500)),
        sa.Column('unit', sa.String(20), server_default='件'),
        sa.Column('suggested_qty', sa.Numeric(10, 4), nullable=False),
        sa.Column('current_stock', sa.Numeric(10, 4), server_default='0'),
        sa.Column('safety_stock', sa.Numeric(10, 4), server_default='0'),
        sa.Column('source_type', sa.String(30), nullable=False),
        sa.Column('source_id', sa.Integer()),
        sa.Column('project_id', sa.Integer()),
        sa.Column('required_date', sa.Date()),
        sa.Column('urgency_level', sa.String(20), server_default='NORMAL'),
        sa.Column('suggested_supplier_id', sa.Integer()),
        sa.Column('ai_confidence', sa.Numeric(5, 2)),
        sa.Column('recommendation_reason', sa.JSON()),
        sa.Column('alternative_suppliers', sa.JSON()),
        sa.Column('estimated_unit_price', sa.Numeric(12, 4)),
        sa.Column('estimated_total_amount', sa.Numeric(14, 2)),
        sa.Column('status', sa.String(20), server_default='PENDING'),
        sa.Column('reviewed_by', sa.Integer()),
        sa.Column('reviewed_at', sa.DateTime()),
        sa.Column('review_note', sa.Text()),
        sa.Column('purchase_order_id', sa.Integer()),
        sa.Column('ordered_at', sa.DateTime()),
        sa.Column('remark', sa.Text()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('suggestion_no'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['suggested_supplier_id'], ['vendors.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id']),
    )
    
    # 索引
    op.create_index('idx_ps_material', 'purchase_suggestions', ['material_id'])
    op.create_index('idx_ps_status', 'purchase_suggestions', ['status'])
    op.create_index('idx_ps_source', 'purchase_suggestions', ['source_type'])
    op.create_index('idx_ps_tenant', 'purchase_suggestions', ['tenant_id'])
    op.create_index('idx_ps_suggested_supplier', 'purchase_suggestions', ['suggested_supplier_id'])
    
    # 2. 供应商报价表
    op.create_table(
        'supplier_quotations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('quotation_no', sa.String(50), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('material_code', sa.String(50), nullable=False),
        sa.Column('material_name', sa.String(200), nullable=False),
        sa.Column('specification', sa.String(500)),
        sa.Column('unit_price', sa.Numeric(12, 4), nullable=False),
        sa.Column('currency', sa.String(10), server_default='CNY'),
        sa.Column('min_order_qty', sa.Numeric(10, 4), server_default='1'),
        sa.Column('lead_time_days', sa.Integer(), server_default='0'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=False),
        sa.Column('payment_terms', sa.String(100)),
        sa.Column('warranty_period', sa.String(50)),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='13'),
        sa.Column('status', sa.String(20), server_default='ACTIVE'),
        sa.Column('is_selected', sa.Boolean(), server_default='false'),
        sa.Column('inquiry_id', sa.Integer()),
        sa.Column('attachments', sa.JSON()),
        sa.Column('remark', sa.Text()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quotation_no'),
        sa.ForeignKeyConstraint(['supplier_id'], ['vendors.id']),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    
    # 索引
    op.create_index('idx_sq_supplier', 'supplier_quotations', ['supplier_id'])
    op.create_index('idx_sq_material', 'supplier_quotations', ['material_id'])
    op.create_index('idx_sq_status', 'supplier_quotations', ['status'])
    op.create_index('idx_sq_tenant', 'supplier_quotations', ['tenant_id'])
    op.create_index('idx_sq_valid_date', 'supplier_quotations', ['valid_from', 'valid_to'])
    
    # 3. 供应商绩效表
    op.create_table(
        'supplier_performances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(50), nullable=False),
        sa.Column('supplier_name', sa.String(200), nullable=False),
        sa.Column('evaluation_period', sa.String(20), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('total_orders', sa.Integer(), server_default='0'),
        sa.Column('total_amount', sa.Numeric(14, 2), server_default='0'),
        sa.Column('on_time_delivery_rate', sa.Numeric(5, 2), server_default='0'),
        sa.Column('on_time_orders', sa.Integer(), server_default='0'),
        sa.Column('late_orders', sa.Integer(), server_default='0'),
        sa.Column('avg_delay_days', sa.Numeric(6, 2), server_default='0'),
        sa.Column('quality_pass_rate', sa.Numeric(5, 2), server_default='0'),
        sa.Column('total_received_qty', sa.Numeric(12, 4), server_default='0'),
        sa.Column('qualified_qty', sa.Numeric(12, 4), server_default='0'),
        sa.Column('rejected_qty', sa.Numeric(12, 4), server_default='0'),
        sa.Column('price_competitiveness', sa.Numeric(5, 2), server_default='0'),
        sa.Column('avg_price_vs_market', sa.Numeric(6, 2), server_default='0'),
        sa.Column('response_speed_score', sa.Numeric(5, 2), server_default='0'),
        sa.Column('avg_response_hours', sa.Numeric(6, 2), server_default='0'),
        sa.Column('service_score', sa.Numeric(5, 2)),
        sa.Column('overall_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('rating', sa.String(2)),
        sa.Column('weight_config', sa.JSON()),
        sa.Column('detail_data', sa.JSON()),
        sa.Column('status', sa.String(20), server_default='CALCULATED'),
        sa.Column('reviewed_by', sa.Integer()),
        sa.Column('reviewed_at', sa.DateTime()),
        sa.Column('review_note', sa.Text()),
        sa.Column('remark', sa.Text()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['vendors.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    
    # 索引
    op.create_index('idx_sp_supplier', 'supplier_performances', ['supplier_id'])
    op.create_index('idx_sp_period', 'supplier_performances', ['evaluation_period'])
    op.create_index('idx_sp_tenant', 'supplier_performances', ['tenant_id'])
    op.create_index('idx_sp_score', 'supplier_performances', ['overall_score'])
    
    # 4. 采购订单跟踪表
    op.create_table(
        'purchase_order_trackings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.String(50), nullable=False),
        sa.Column('event_type', sa.String(30), nullable=False),
        sa.Column('event_time', sa.DateTime(), nullable=False),
        sa.Column('event_description', sa.Text()),
        sa.Column('old_status', sa.String(20)),
        sa.Column('new_status', sa.String(20)),
        sa.Column('tracking_no', sa.String(100)),
        sa.Column('logistics_company', sa.String(100)),
        sa.Column('estimated_arrival', sa.Date()),
        sa.Column('attachments', sa.JSON()),
        sa.Column('note', sa.Text()),
        sa.Column('operator_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['purchase_orders.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id']),
    )
    
    # 索引
    op.create_index('idx_pot_order', 'purchase_order_trackings', ['order_id'])
    op.create_index('idx_pot_tenant', 'purchase_order_trackings', ['tenant_id'])
    op.create_index('idx_pot_event_type', 'purchase_order_trackings', ['event_type'])


def downgrade():
    """删除表"""
    op.drop_table('purchase_order_trackings')
    op.drop_table('supplier_performances')
    op.drop_table('supplier_quotations')
    op.drop_table('purchase_suggestions')
