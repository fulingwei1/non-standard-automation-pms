"""project delivery schedule

Revision ID: 20260328
Revises: 
Create Date: 2026-03-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260328'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 项目交付排产计划主表
    op.create_table('project_delivery_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键 ID'),
        sa.Column('schedule_no', sa.String(50), nullable=False, comment='计划编号 PDS-2026-001'),
        sa.Column('schedule_name', sa.String(200), nullable=False, comment='计划名称'),
        sa.Column('lead_id', sa.Integer(), nullable=True, comment='商机 ID'),
        sa.Column('project_id', sa.Integer(), nullable=True, comment='项目 ID'),
        sa.Column('project_template_id', sa.Integer(), nullable=True, comment='项目模板 ID'),
        sa.Column('contract_id', sa.Integer(), nullable=True, comment='合同 ID'),
        sa.Column('version', sa.String(20), default='V1.0', comment='版本号'),
        sa.Column('version_comment', sa.String(500), nullable=True, comment='版本说明'),
        sa.Column('status', sa.String(20), default='DRAFT', comment='状态'),
        sa.Column('usage_type', sa.String(20), default='INTERNAL', comment='使用类型'),
        sa.Column('initiator_id', sa.Integer(), nullable=False, comment='发起人 ID'),
        sa.Column('initiator_name', sa.String(100), nullable=True, comment='发起人姓名'),
        sa.Column('confirmed_by', sa.Integer(), nullable=True, comment='确认人 ID'),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True, comment='确认时间'),
        sa.Column('contract_signed_at', sa.DateTime(), nullable=True, comment='合同签订时间'),
        sa.Column('is_pre_contract', sa.Boolean(), default=True, comment='是否合同签订前创建'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='是否当前有效版本'),
        sa.Column('parent_version_id', sa.Integer(), nullable=True, comment='父版本 ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schedule_no'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['project_template_id'], ['project_templates.id']),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id']),
        sa.ForeignKeyConstraint(['initiator_id'], ['users.id']),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['parent_version_id'], ['project_delivery_schedules.id']),
    )
    op.create_index('idx_pds_lead', 'project_delivery_schedules', ['lead_id'])
    op.create_index('idx_pds_project', 'project_delivery_schedules', ['project_id'])
    op.create_index('idx_pds_status', 'project_delivery_schedules', ['status'])
    op.create_index('idx_pds_usage', 'project_delivery_schedules', ['usage_type'])
    op.create_index('idx_pds_active', 'project_delivery_schedules', ['is_active'])

    # 交付任务表
    op.create_table('project_delivery_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('task_no', sa.String(50), nullable=True),
        sa.Column('task_type', sa.String(30), nullable=False),
        sa.Column('task_name', sa.String(200), nullable=False),
        sa.Column('task_description', sa.Text(), nullable=True),
        sa.Column('machine_name', sa.String(200), nullable=True),
        sa.Column('module_name', sa.String(200), nullable=True),
        sa.Column('parent_task_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.Integer(), default=1),
        sa.Column('assigned_engineer_id', sa.Integer(), nullable=True),
        sa.Column('assigned_engineer_name', sa.String(100), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('department_name', sa.String(100), nullable=True),
        sa.Column('planned_start', sa.Date(), nullable=False),
        sa.Column('planned_end', sa.Date(), nullable=False),
        sa.Column('estimated_hours', sa.Numeric(10, 2), default=0),
        sa.Column('predecessor_tasks', mysql.JSON(), default=list),
        sa.Column('dependency_type', sa.String(10), default='FS'),
        sa.Column('lag_days', sa.Integer(), default=0),
        sa.Column('has_conflict', sa.Boolean(), default=False),
        sa.Column('conflict_details', mysql.JSON(), nullable=True),
        sa.Column('status', sa.String(20), default='PENDING'),
        sa.Column('progress_pct', sa.Numeric(5, 2), default=0),
        sa.Column('filled_by', sa.Integer(), nullable=True),
        sa.Column('filled_by_name', sa.String(100), nullable=True),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['project_delivery_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_task_id'], ['project_delivery_tasks.id']),
        sa.ForeignKeyConstraint(['assigned_engineer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['filled_by'], ['users.id']),
    )
    op.create_index('idx_pdt_schedule', 'project_delivery_tasks', ['schedule_id'])
    op.create_index('idx_pdt_type', 'project_delivery_tasks', ['task_type'])
    op.create_index('idx_pdt_engineer', 'project_delivery_tasks', ['assigned_engineer_id'])
    op.create_index('idx_pdt_status', 'project_delivery_tasks', ['status'])

    # 长周期采购表
    op.create_table('project_delivery_long_cycle_purchases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('item_no', sa.String(50), nullable=True),
        sa.Column('material_name', sa.String(200), nullable=False),
        sa.Column('material_spec', sa.String(500), nullable=True),
        sa.Column('material_category', sa.String(100), nullable=True),
        sa.Column('supplier', sa.String(200), nullable=True),
        sa.Column('supplier_contact', sa.String(200), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=False),
        sa.Column('planned_order_date', sa.Date(), nullable=True),
        sa.Column('planned_arrival_date', sa.Date(), nullable=True),
        sa.Column('is_critical', sa.Boolean(), default=False),
        sa.Column('has_conflict', sa.Boolean(), default=False),
        sa.Column('conflict_reason', sa.String(500), nullable=True),
        sa.Column('filled_by', sa.Integer(), nullable=True),
        sa.Column('filled_by_name', sa.String(100), nullable=True),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['project_delivery_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['filled_by'], ['users.id']),
    )
    op.create_index('idx_pdlcp_schedule', 'project_delivery_long_cycle_purchases', ['schedule_id'])
    op.create_index('idx_pdlcp_critical', 'project_delivery_long_cycle_purchases', ['is_critical'])

    # 机械设计任务表
    op.create_table('project_delivery_mechanical_designs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('design_type', sa.String(30), nullable=False),
        sa.Column('machine_name', sa.String(200), nullable=True),
        sa.Column('module_name', sa.String(200), nullable=True),
        sa.Column('designer_id', sa.Integer(), nullable=True),
        sa.Column('designer_name', sa.String(100), nullable=True),
        sa.Column('planned_start', sa.Date(), nullable=False),
        sa.Column('planned_end', sa.Date(), nullable=False),
        sa.Column('estimated_hours', sa.Numeric(10, 2), default=0),
        sa.Column('deliverables', mysql.JSON(), nullable=True),
        sa.Column('status', sa.String(20), default='PENDING'),
        sa.Column('filled_by', sa.Integer(), nullable=True),
        sa.Column('filled_by_name', sa.String(100), nullable=True),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['project_delivery_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['designer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['filled_by'], ['users.id']),
    )
    op.create_index('idx_pdmd_schedule', 'project_delivery_mechanical_designs', ['schedule_id'])
    op.create_index('idx_pdmd_type', 'project_delivery_mechanical_designs', ['design_type'])

    # 变更日志表
    op.create_table('project_delivery_change_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('change_no', sa.String(50), nullable=True),
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('version_from', sa.String(20), nullable=True),
        sa.Column('version_to', sa.String(20), nullable=True),
        sa.Column('old_data', mysql.JSON(), nullable=True),
        sa.Column('new_data', mysql.JSON(), nullable=True),
        sa.Column('change_reason', sa.String(500), nullable=True),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('changed_by_name', sa.String(100), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('notified_users', mysql.JSON(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['project_delivery_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id']),
    )
    op.create_index('idx_pdcl_schedule', 'project_delivery_change_logs', ['schedule_id'])
    op.create_index('idx_pdcl_type', 'project_delivery_change_logs', ['change_type'])

    # 任务依赖关系表
    op.create_table('project_delivery_dependencies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('predecessor_task_id', sa.Integer(), nullable=False),
        sa.Column('successor_task_id', sa.Integer(), nullable=False),
        sa.Column('dependency_type', sa.String(10), default='FS'),
        sa.Column('lag_days', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('predecessor_task_id', 'successor_task_id', name='uq_dependency'),
        sa.ForeignKeyConstraint(['schedule_id'], ['project_delivery_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['predecessor_task_id'], ['project_delivery_tasks.id']),
        sa.ForeignKeyConstraint(['successor_task_id'], ['project_delivery_tasks.id']),
    )
    op.create_index('idx_pdd_schedule', 'project_delivery_dependencies', ['schedule_id'])


def downgrade() -> None:
    op.drop_table('project_delivery_dependencies')
    op.drop_table('project_delivery_change_logs')
    op.drop_table('project_delivery_mechanical_designs')
    op.drop_table('project_delivery_long_cycle_purchases')
    op.drop_table('project_delivery_tasks')
    op.drop_table('project_delivery_schedules')
