"""add timesheet reminder tables

Revision ID: 20260214185031
Revises: 
Create Date: 2026-02-14 18:50:31.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260214185031'
down_revision = None  # 需要根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    # 创建工时提醒规则配置表
    op.create_table(
        'timesheet_reminder_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('rule_code', sa.String(length=50), nullable=False, comment='规则编码'),
        sa.Column('rule_name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('reminder_type', sa.Enum(
            'MISSING_TIMESHEET',
            'APPROVAL_TIMEOUT',
            'ANOMALY_TIMESHEET',
            'WEEKEND_WORK',
            'HOLIDAY_WORK',
            'SYNC_FAILURE',
            name='remindertypeenum'
        ), nullable=False, comment='提醒类型'),
        sa.Column('apply_to_departments', sa.JSON(), nullable=True, comment='适用部门ID列表'),
        sa.Column('apply_to_roles', sa.JSON(), nullable=True, comment='适用角色ID列表'),
        sa.Column('apply_to_users', sa.JSON(), nullable=True, comment='适用用户ID列表'),
        sa.Column('rule_parameters', sa.JSON(), nullable=True, comment='规则参数'),
        sa.Column('notification_channels', sa.JSON(), nullable=True, comment='通知渠道列表'),
        sa.Column('notification_template', sa.Text(), nullable=True, comment='通知模板'),
        sa.Column('remind_frequency', sa.String(length=20), nullable=True, comment='提醒频率'),
        sa.Column('max_reminders_per_day', sa.Integer(), nullable=True, comment='每日最大提醒次数'),
        sa.Column('priority', sa.String(length=20), nullable=True, comment='优先级'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_code'),
        comment='工时提醒规则配置表'
    )
    op.create_index('idx_reminder_config_type', 'timesheet_reminder_config', ['reminder_type'])
    op.create_index('idx_reminder_config_active', 'timesheet_reminder_config', ['is_active'])

    # 创建工时提醒记录表
    op.create_table(
        'timesheet_reminder_record',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('reminder_no', sa.String(length=50), nullable=False, comment='提醒编号'),
        sa.Column('reminder_type', sa.Enum(
            'MISSING_TIMESHEET',
            'APPROVAL_TIMEOUT',
            'ANOMALY_TIMESHEET',
            'WEEKEND_WORK',
            'HOLIDAY_WORK',
            'SYNC_FAILURE',
            name='remindertypeenum'
        ), nullable=False, comment='提醒类型'),
        sa.Column('config_id', sa.Integer(), nullable=True, comment='关联配置ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('user_name', sa.String(length=50), nullable=True, comment='用户姓名'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='提醒标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='提醒内容'),
        sa.Column('source_type', sa.String(length=50), nullable=True, comment='来源类型'),
        sa.Column('source_id', sa.Integer(), nullable=True, comment='来源ID'),
        sa.Column('extra_data', sa.JSON(), nullable=True, comment='额外数据'),
        sa.Column('status', sa.Enum(
            'PENDING',
            'SENT',
            'READ',
            'DISMISSED',
            'RESOLVED',
            name='reminderstatusenum'
        ), nullable=True, comment='提醒状态'),
        sa.Column('notification_channels', sa.JSON(), nullable=True, comment='已发送通知渠道'),
        sa.Column('sent_at', sa.DateTime(), nullable=True, comment='发送时间'),
        sa.Column('read_at', sa.DateTime(), nullable=True, comment='已读时间'),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True, comment='忽略时间'),
        sa.Column('dismissed_by', sa.Integer(), nullable=True, comment='忽略人ID'),
        sa.Column('dismissed_reason', sa.Text(), nullable=True, comment='忽略原因'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True, comment='解决时间'),
        sa.Column('priority', sa.String(length=20), nullable=True, comment='优先级'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['config_id'], ['timesheet_reminder_config.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['dismissed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reminder_no'),
        comment='工时提醒记录表'
    )
    op.create_index('idx_reminder_record_user', 'timesheet_reminder_record', ['user_id'])
    op.create_index('idx_reminder_record_type', 'timesheet_reminder_record', ['reminder_type'])
    op.create_index('idx_reminder_record_status', 'timesheet_reminder_record', ['status'])
    op.create_index('idx_reminder_record_sent', 'timesheet_reminder_record', ['sent_at'])
    op.create_index('idx_reminder_record_source', 'timesheet_reminder_record', ['source_type', 'source_id'])

    # 创建异常工时检测记录表
    op.create_table(
        'timesheet_anomaly_record',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('timesheet_id', sa.Integer(), nullable=False, comment='工时记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('user_name', sa.String(length=50), nullable=True, comment='用户姓名'),
        sa.Column('anomaly_type', sa.Enum(
            'DAILY_OVER_12',
            'DAILY_INVALID',
            'WEEKLY_OVER_60',
            'NO_REST_7DAYS',
            'PROGRESS_MISMATCH',
            name='anomalytypeenum'
        ), nullable=False, comment='异常类型'),
        sa.Column('description', sa.Text(), nullable=False, comment='异常描述'),
        sa.Column('anomaly_data', sa.JSON(), nullable=True, comment='异常数据'),
        sa.Column('severity', sa.String(length=20), nullable=True, comment='严重程度'),
        sa.Column('detected_at', sa.DateTime(), nullable=False, comment='检测时间'),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, comment='是否已解决'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True, comment='解决时间'),
        sa.Column('resolved_by', sa.Integer(), nullable=True, comment='解决人ID'),
        sa.Column('resolution_note', sa.Text(), nullable=True, comment='解决说明'),
        sa.Column('reminder_id', sa.Integer(), nullable=True, comment='关联提醒记录ID'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['timesheet_id'], ['timesheet.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reminder_id'], ['timesheet_reminder_record.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='异常工时检测记录表'
    )
    op.create_index('idx_anomaly_timesheet', 'timesheet_anomaly_record', ['timesheet_id'])
    op.create_index('idx_anomaly_user', 'timesheet_anomaly_record', ['user_id'])
    op.create_index('idx_anomaly_type', 'timesheet_anomaly_record', ['anomaly_type'])
    op.create_index('idx_anomaly_resolved', 'timesheet_anomaly_record', ['is_resolved'])
    op.create_index('idx_anomaly_detected', 'timesheet_anomaly_record', ['detected_at'])


def downgrade():
    # 删除索引和表（逆序）
    op.drop_index('idx_anomaly_detected', table_name='timesheet_anomaly_record')
    op.drop_index('idx_anomaly_resolved', table_name='timesheet_anomaly_record')
    op.drop_index('idx_anomaly_type', table_name='timesheet_anomaly_record')
    op.drop_index('idx_anomaly_user', table_name='timesheet_anomaly_record')
    op.drop_index('idx_anomaly_timesheet', table_name='timesheet_anomaly_record')
    op.drop_table('timesheet_anomaly_record')

    op.drop_index('idx_reminder_record_source', table_name='timesheet_reminder_record')
    op.drop_index('idx_reminder_record_sent', table_name='timesheet_reminder_record')
    op.drop_index('idx_reminder_record_status', table_name='timesheet_reminder_record')
    op.drop_index('idx_reminder_record_type', table_name='timesheet_reminder_record')
    op.drop_index('idx_reminder_record_user', table_name='timesheet_reminder_record')
    op.drop_table('timesheet_reminder_record')

    op.drop_index('idx_reminder_config_active', table_name='timesheet_reminder_config')
    op.drop_index('idx_reminder_config_type', table_name='timesheet_reminder_config')
    op.drop_table('timesheet_reminder_config')
