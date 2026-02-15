"""销售团队管理 - 组织架构与目标管理

Revision ID: 20260215_sales_team_management
Revises: 
Create Date: 2026-02-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260215_sales_team_management'
down_revision = None  # 更新为实际的上一个迁移ID
branch_labels = None
depends_on = None


def upgrade():
    # 创建 sales_targets_v2 表
    op.create_table(
        'sales_targets_v2',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='目标ID'),
        sa.Column('target_period', sa.Enum('year', 'quarter', 'month', name='targetperiodenumv2'), nullable=False, comment='目标期间(year/quarter/month)'),
        sa.Column('target_year', sa.Integer(), nullable=False, comment='目标年份'),
        sa.Column('target_month', sa.Integer(), nullable=True, comment='目标月份(1-12)'),
        sa.Column('target_quarter', sa.Integer(), nullable=True, comment='目标季度(1-4)'),
        sa.Column('target_type', sa.Enum('company', 'team', 'personal', name='targettypeenumv2'), nullable=False, comment='目标类型(company/team/personal)'),
        sa.Column('team_id', sa.Integer(), nullable=True, comment='团队ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('sales_target', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='销售额目标'),
        sa.Column('payment_target', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='回款目标'),
        sa.Column('new_customer_target', sa.Integer(), nullable=False, server_default='0', comment='新客户数目标'),
        sa.Column('lead_target', sa.Integer(), nullable=False, server_default='0', comment='线索数目标'),
        sa.Column('opportunity_target', sa.Integer(), nullable=False, server_default='0', comment='商机数目标'),
        sa.Column('deal_target', sa.Integer(), nullable=False, server_default='0', comment='签单数目标'),
        sa.Column('actual_sales', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='实际销售额'),
        sa.Column('actual_payment', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0', comment='实际回款'),
        sa.Column('actual_new_customers', sa.Integer(), nullable=False, server_default='0', comment='实际新客户数'),
        sa.Column('actual_leads', sa.Integer(), nullable=False, server_default='0', comment='实际线索数'),
        sa.Column('actual_opportunities', sa.Integer(), nullable=False, server_default='0', comment='实际商机数'),
        sa.Column('actual_deals', sa.Integer(), nullable=False, server_default='0', comment='实际签单数'),
        sa.Column('completion_rate', sa.Numeric(precision=5, scale=2), server_default='0', comment='完成率(%)'),
        sa.Column('parent_target_id', sa.Integer(), nullable=True, comment='上级目标ID（用于目标分解）'),
        sa.Column('description', sa.Text(), comment='目标描述'),
        sa.Column('remark', sa.Text(), comment='备注'),
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.CheckConstraint(
            """
            (target_type = 'company' AND team_id IS NULL AND user_id IS NULL) OR
            (target_type = 'team' AND team_id IS NOT NULL AND user_id IS NULL) OR
            (target_type = 'personal' AND user_id IS NOT NULL)
            """,
            name='chk_target_type_v2'
        ),
        sa.ForeignKeyConstraint(['team_id'], ['sales_teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_target_id'], ['sales_targets_v2.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_sales_target_v2_team', 'sales_targets_v2', ['team_id'])
    op.create_index('idx_sales_target_v2_user', 'sales_targets_v2', ['user_id'])
    op.create_index('idx_sales_target_v2_period', 'sales_targets_v2', ['target_year', 'target_month'])
    op.create_index('idx_sales_target_v2_parent', 'sales_targets_v2', ['parent_target_id'])
    op.create_index('idx_sales_target_v2_type', 'sales_targets_v2', ['target_type'])
    
    # 创建 target_breakdown_logs 表
    op.create_table(
        'target_breakdown_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='日志ID'),
        sa.Column('parent_target_id', sa.Integer(), nullable=False, comment='上级目标ID'),
        sa.Column('breakdown_type', sa.String(20), nullable=False, comment='分解类型：AUTO(自动分解)/MANUAL(手动分解)'),
        sa.Column('breakdown_method', sa.String(50), comment='分解方法：EQUAL(平均分配)/RATIO(按比例)/CUSTOM(自定义)'),
        sa.Column('breakdown_details', sa.Text(), comment='分解详情(JSON格式)'),
        sa.Column('created_by', sa.Integer(), comment='分解操作人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['parent_target_id'], ['sales_targets_v2.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_breakdown_log_parent', 'target_breakdown_logs', ['parent_target_id'])
    op.create_index('idx_breakdown_log_created', 'target_breakdown_logs', ['created_at'])
    
    # 创建 sales_regions 表
    op.create_table(
        'sales_regions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='区域ID'),
        sa.Column('region_code', sa.String(50), unique=True, nullable=False, comment='区域编码'),
        sa.Column('region_name', sa.String(100), nullable=False, comment='区域名称'),
        sa.Column('parent_region_id', sa.Integer(), nullable=True, comment='上级区域ID'),
        sa.Column('level', sa.Integer(), server_default='1', comment='区域层级'),
        sa.Column('provinces', sa.JSON(), comment='包含的省份(JSON数组)'),
        sa.Column('cities', sa.JSON(), comment='包含的城市(JSON数组)'),
        sa.Column('team_id', sa.Integer(), nullable=True, comment='负责团队ID'),
        sa.Column('leader_id', sa.Integer(), nullable=True, comment='负责人ID'),
        sa.Column('description', sa.Text(), comment='区域描述'),
        sa.Column('is_active', sa.Boolean(), server_default='1', comment='是否启用'),
        sa.Column('sort_order', sa.Integer(), server_default='0', comment='排序序号'),
        sa.Column('created_by', sa.Integer(), comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['parent_region_id'], ['sales_regions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['team_id'], ['sales_teams.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['leader_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_sales_region_code', 'sales_regions', ['region_code'])
    op.create_index('idx_sales_region_parent', 'sales_regions', ['parent_region_id'])
    op.create_index('idx_sales_region_team', 'sales_regions', ['team_id'])
    op.create_index('idx_sales_region_leader', 'sales_regions', ['leader_id'])
    op.create_index('idx_sales_region_active', 'sales_regions', ['is_active'])


def downgrade():
    # 删除索引
    op.drop_index('idx_sales_region_active', 'sales_regions')
    op.drop_index('idx_sales_region_leader', 'sales_regions')
    op.drop_index('idx_sales_region_team', 'sales_regions')
    op.drop_index('idx_sales_region_parent', 'sales_regions')
    op.drop_index('idx_sales_region_code', 'sales_regions')
    
    op.drop_index('idx_breakdown_log_created', 'target_breakdown_logs')
    op.drop_index('idx_breakdown_log_parent', 'target_breakdown_logs')
    
    op.drop_index('idx_sales_target_v2_type', 'sales_targets_v2')
    op.drop_index('idx_sales_target_v2_parent', 'sales_targets_v2')
    op.drop_index('idx_sales_target_v2_period', 'sales_targets_v2')
    op.drop_index('idx_sales_target_v2_user', 'sales_targets_v2')
    op.drop_index('idx_sales_target_v2_team', 'sales_targets_v2')
    
    # 删除表
    op.drop_table('sales_regions')
    op.drop_table('target_breakdown_logs')
    op.drop_table('sales_targets_v2')
