# -*- coding: utf-8 -*-
"""
添加库存跟踪系统表
Team 2: 物料全流程跟踪系统

Revision ID: 20260216_inventory_tracking
Create Date: 2026-02-16 08:30:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '20260216_inventory_tracking'
down_revision = None  # 设置为前一个迁移的revision
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    
    # 1. MaterialTransaction - 物料交易记录表
    op.create_table(
        'material_transaction',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('material_id', sa.Integer(), nullable=False, comment='物料ID'),
        sa.Column('material_code', sa.String(50), nullable=False, comment='物料编码(冗余)'),
        sa.Column('material_name', sa.String(200), nullable=False, comment='物料名称(冗余)'),
        sa.Column('transaction_type', sa.String(20), nullable=False, comment='交易类型'),
        sa.Column('quantity', sa.Numeric(14, 4), nullable=False, comment='交易数量'),
        sa.Column('unit', sa.String(20), default='件', comment='单位'),
        sa.Column('unit_price', sa.Numeric(12, 4), default=0, comment='单价'),
        sa.Column('total_amount', sa.Numeric(14, 2), default=0, comment='总金额'),
        sa.Column('source_location', sa.String(100), comment='来源位置/仓库'),
        sa.Column('target_location', sa.String(100), comment='目标位置/仓库'),
        sa.Column('batch_number', sa.String(100), comment='批次号'),
        sa.Column('related_order_id', sa.Integer(), comment='关联订单ID'),
        sa.Column('related_order_type', sa.String(30), comment='关联单据类型'),
        sa.Column('related_order_no', sa.String(50), comment='关联单据编号'),
        sa.Column('transaction_date', sa.DateTime(), nullable=False, comment='交易时间'),
        sa.Column('operator_id', sa.Integer(), comment='操作人ID'),
        sa.Column('remark', sa.Text(), comment='备注说明'),
        sa.Column('cost_method', sa.String(20), default='WEIGHTED_AVG', comment='成本核算方法'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id']),
        
        comment='物料交易记录表'
    )
    
    # 创建索引
    op.create_index('idx_mat_trans_material', 'material_transaction', ['material_id'])
    op.create_index('idx_mat_trans_type', 'material_transaction', ['transaction_type'])
    op.create_index('idx_mat_trans_date', 'material_transaction', ['transaction_date'])
    op.create_index('idx_mat_trans_batch', 'material_transaction', ['batch_number'])
    op.create_index('idx_mat_trans_order', 'material_transaction', ['related_order_id'])
    op.create_index('idx_mat_trans_location', 'material_transaction', ['source_location', 'target_location'])
    
    # 2. MaterialStock - 物料库存表
    op.create_table(
        'material_stock',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('material_id', sa.Integer(), nullable=False, comment='物料ID'),
        sa.Column('material_code', sa.String(50), nullable=False, comment='物料编码(冗余)'),
        sa.Column('material_name', sa.String(200), nullable=False, comment='物料名称(冗余)'),
        sa.Column('location', sa.String(100), nullable=False, comment='仓库位置'),
        sa.Column('batch_number', sa.String(100), comment='批次号'),
        sa.Column('quantity', sa.Numeric(14, 4), nullable=False, default=0, comment='库存总数量'),
        sa.Column('available_quantity', sa.Numeric(14, 4), nullable=False, default=0, comment='可用数量(总数-预留)'),
        sa.Column('reserved_quantity', sa.Numeric(14, 4), default=0, comment='预留数量'),
        sa.Column('unit', sa.String(20), default='件', comment='单位'),
        sa.Column('unit_price', sa.Numeric(12, 4), default=0, comment='单价(加权平均)'),
        sa.Column('total_value', sa.Numeric(14, 2), default=0, comment='库存总价值'),
        sa.Column('production_date', sa.Date(), comment='生产日期'),
        sa.Column('expire_date', sa.Date(), comment='失效日期'),
        sa.Column('status', sa.String(20), default='NORMAL', comment='状态'),
        sa.Column('last_in_date', sa.DateTime(), comment='最后入库时间'),
        sa.Column('last_out_date', sa.DateTime(), comment='最后出库时间'),
        sa.Column('last_update', sa.DateTime(), default=sa.func.now(), comment='最后更新时间'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        
        comment='物料库存表'
    )
    
    # 创建索引和唯一约束
    op.create_index('idx_mat_stock_material', 'material_stock', ['material_id'])
    op.create_index('idx_mat_stock_location', 'material_stock', ['location'])
    op.create_index('idx_mat_stock_batch', 'material_stock', ['batch_number'])
    op.create_index('idx_mat_stock_available', 'material_stock', ['available_quantity'])
    op.create_index('idx_mat_stock_unique', 'material_stock', ['material_id', 'location', 'batch_number'], unique=True)
    
    # 3. MaterialReservation - 物料预留表
    op.create_table(
        'material_reservation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('reservation_no', sa.String(50), unique=True, nullable=False, comment='预留单号'),
        sa.Column('material_id', sa.Integer(), nullable=False, comment='物料ID'),
        sa.Column('stock_id', sa.Integer(), comment='库存ID'),
        sa.Column('reserved_quantity', sa.Numeric(14, 4), nullable=False, comment='预留数量'),
        sa.Column('used_quantity', sa.Numeric(14, 4), default=0, comment='已使用数量'),
        sa.Column('remaining_quantity', sa.Numeric(14, 4), comment='剩余数量'),
        sa.Column('project_id', sa.Integer(), comment='项目ID'),
        sa.Column('work_order_id', sa.Integer(), comment='工单ID'),
        sa.Column('reservation_date', sa.DateTime(), nullable=False, comment='预留时间'),
        sa.Column('expected_use_date', sa.Date(), comment='预计使用日期'),
        sa.Column('actual_use_date', sa.Date(), comment='实际使用日期'),
        sa.Column('status', sa.String(20), default='ACTIVE', comment='状态'),
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        sa.Column('cancelled_by', sa.Integer(), comment='取消人ID'),
        sa.Column('cancelled_at', sa.DateTime(), comment='取消时间'),
        sa.Column('cancel_reason', sa.Text(), comment='取消原因'),
        sa.Column('remark', sa.Text(), comment='备注'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['stock_id'], ['material_stock.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_order.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id']),
        
        comment='物料预留表'
    )
    
    # 创建索引
    op.create_index('idx_mat_res_material', 'material_reservation', ['material_id'])
    op.create_index('idx_mat_res_stock', 'material_reservation', ['stock_id'])
    op.create_index('idx_mat_res_project', 'material_reservation', ['project_id'])
    op.create_index('idx_mat_res_status', 'material_reservation', ['status'])
    op.create_index('idx_mat_res_date', 'material_reservation', ['expected_use_date'])
    
    # 4. StockCountTask - 库存盘点任务表
    op.create_table(
        'stock_count_task',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('task_no', sa.String(50), unique=True, nullable=False, comment='盘点任务号'),
        sa.Column('count_type', sa.String(20), default='FULL', comment='盘点类型'),
        sa.Column('location', sa.String(100), comment='盘点位置/仓库'),
        sa.Column('category_id', sa.Integer(), comment='物料分类ID'),
        sa.Column('count_date', sa.Date(), nullable=False, comment='盘点日期'),
        sa.Column('start_time', sa.DateTime(), comment='开始时间'),
        sa.Column('end_time', sa.DateTime(), comment='结束时间'),
        sa.Column('status', sa.String(20), default='PENDING', comment='状态'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('assigned_to', sa.Integer(), comment='盘点人ID'),
        sa.Column('approved_by', sa.Integer(), comment='审批人ID'),
        sa.Column('approved_at', sa.DateTime(), comment='审批时间'),
        sa.Column('total_items', sa.Integer(), default=0, comment='总物料数'),
        sa.Column('counted_items', sa.Integer(), default=0, comment='已盘点数'),
        sa.Column('matched_items', sa.Integer(), default=0, comment='账实相符数'),
        sa.Column('diff_items', sa.Integer(), default=0, comment='差异物料数'),
        sa.Column('total_diff_value', sa.Numeric(14, 2), default=0, comment='总差异金额'),
        sa.Column('remark', sa.Text(), comment='备注说明'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['category_id'], ['material_categories.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        
        comment='库存盘点任务表'
    )
    
    # 创建索引
    op.create_index('idx_count_task_no', 'stock_count_task', ['task_no'])
    op.create_index('idx_count_task_location', 'stock_count_task', ['location'])
    op.create_index('idx_count_task_status', 'stock_count_task', ['status'])
    op.create_index('idx_count_task_date', 'stock_count_task', ['count_date'])
    
    # 5. StockCountDetail - 库存盘点明细表
    op.create_table(
        'stock_count_detail',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('task_id', sa.Integer(), nullable=False, comment='盘点任务ID'),
        sa.Column('material_id', sa.Integer(), nullable=False, comment='物料ID'),
        sa.Column('material_code', sa.String(50), nullable=False, comment='物料编码(冗余)'),
        sa.Column('material_name', sa.String(200), nullable=False, comment='物料名称(冗余)'),
        sa.Column('location', sa.String(100), comment='仓库位置'),
        sa.Column('batch_number', sa.String(100), comment='批次号'),
        sa.Column('system_quantity', sa.Numeric(14, 4), nullable=False, comment='系统数量(账面)'),
        sa.Column('actual_quantity', sa.Numeric(14, 4), comment='实盘数量'),
        sa.Column('difference', sa.Numeric(14, 4), comment='差异数量(实盘-账面)'),
        sa.Column('difference_rate', sa.Numeric(5, 2), comment='差异率(%)'),
        sa.Column('unit_price', sa.Numeric(12, 4), comment='单价'),
        sa.Column('diff_value', sa.Numeric(14, 2), comment='差异金额'),
        sa.Column('status', sa.String(20), default='PENDING', comment='状态'),
        sa.Column('counted_by', sa.Integer(), comment='盘点人ID'),
        sa.Column('counted_at', sa.DateTime(), comment='盘点时间'),
        sa.Column('is_recounted', sa.Boolean(), default=False, comment='是否复盘'),
        sa.Column('recount_reason', sa.Text(), comment='复盘原因'),
        sa.Column('remark', sa.Text(), comment='备注'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['task_id'], ['stock_count_task.id']),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['counted_by'], ['users.id']),
        
        comment='库存盘点明细表'
    )
    
    # 创建索引
    op.create_index('idx_count_detail_task', 'stock_count_detail', ['task_id'])
    op.create_index('idx_count_detail_material', 'stock_count_detail', ['material_id'])
    op.create_index('idx_count_detail_status', 'stock_count_detail', ['status'])
    
    # 6. StockAdjustment - 库存调整表
    op.create_table(
        'stock_adjustment',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('adjustment_no', sa.String(50), unique=True, nullable=False, comment='调整单号'),
        sa.Column('material_id', sa.Integer(), nullable=False, comment='物料ID'),
        sa.Column('material_code', sa.String(50), nullable=False, comment='物料编码(冗余)'),
        sa.Column('material_name', sa.String(200), nullable=False, comment='物料名称(冗余)'),
        sa.Column('location', sa.String(100), nullable=False, comment='仓库位置'),
        sa.Column('batch_number', sa.String(100), comment='批次号'),
        sa.Column('original_quantity', sa.Numeric(14, 4), nullable=False, comment='账面数量'),
        sa.Column('actual_quantity', sa.Numeric(14, 4), nullable=False, comment='实盘数量'),
        sa.Column('difference', sa.Numeric(14, 4), nullable=False, comment='差异数量(实盘-账面)'),
        sa.Column('difference_rate', sa.Numeric(5, 2), comment='差异率(%)'),
        sa.Column('adjustment_type', sa.String(20), nullable=False, comment='调整类型'),
        sa.Column('reason', sa.Text(), nullable=False, comment='调整原因'),
        sa.Column('adjustment_date', sa.DateTime(), nullable=False, comment='调整时间'),
        sa.Column('operator_id', sa.Integer(), nullable=False, comment='操作人ID'),
        sa.Column('status', sa.String(20), default='PENDING', comment='状态'),
        sa.Column('approved_by', sa.Integer(), comment='审批人ID'),
        sa.Column('approved_at', sa.DateTime(), comment='审批时间'),
        sa.Column('approval_comment', sa.Text(), comment='审批意见'),
        sa.Column('count_task_id', sa.Integer(), comment='盘点任务ID'),
        sa.Column('unit_price', sa.Numeric(12, 4), comment='单价'),
        sa.Column('total_impact', sa.Numeric(14, 2), comment='总金额影响'),
        sa.Column('remark', sa.Text(), comment='备注'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.ForeignKeyConstraint(['count_task_id'], ['stock_count_task.id']),
        
        comment='库存调整表'
    )
    
    # 创建索引
    op.create_index('idx_stock_adj_material', 'stock_adjustment', ['material_id'])
    op.create_index('idx_stock_adj_location', 'stock_adjustment', ['location'])
    op.create_index('idx_stock_adj_type', 'stock_adjustment', ['adjustment_type'])
    op.create_index('idx_stock_adj_date', 'stock_adjustment', ['adjustment_date'])
    op.create_index('idx_stock_adj_status', 'stock_adjustment', ['status'])


def downgrade():
    """降级数据库"""
    op.drop_table('stock_adjustment')
    op.drop_table('stock_count_detail')
    op.drop_table('stock_count_task')
    op.drop_table('material_reservation')
    op.drop_table('material_stock')
    op.drop_table('material_transaction')
