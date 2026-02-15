"""进度偏差预警系统 - 预测、方案、预警表

Revision ID: 20260215_schedule_prediction_system
Revises: 
Create Date: 2026-02-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20260215_schedule_prediction_system'
down_revision = None  # 更新为实际的上一个迁移ID
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库：创建进度预测系统相关表"""
    
    # ==================== 项目进度预测记录表 ====================
    op.create_table(
        'project_schedule_prediction',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('prediction_date', sa.DateTime(), nullable=False, comment='预测时间'),
        
        # 预测结果
        sa.Column('predicted_completion_date', sa.Date(), comment='预测完成日期'),
        sa.Column('delay_days', sa.Integer(), comment='预计延期天数'),
        sa.Column('confidence', sa.DECIMAL(5, 2), comment='置信度 (0-1)'),
        sa.Column('risk_level', sa.String(20), comment='风险等级: low/medium/high/critical'),
        
        # 特征数据和详情
        sa.Column('features', sa.JSON(), comment='预测特征数据'),
        sa.Column('prediction_details', sa.JSON(), comment='详细预测结果'),
        sa.Column('model_version', sa.String(50), comment='AI模型版本'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        comment='项目进度预测记录表'
    )
    
    # 创建索引
    op.create_index('idx_project_prediction_date', 'project_schedule_prediction', ['project_id', 'prediction_date'])
    op.create_index('idx_risk_level', 'project_schedule_prediction', ['risk_level'])
    op.create_index('idx_prediction_date', 'project_schedule_prediction', ['prediction_date'])
    
    # ==================== 赶工方案表 ====================
    op.create_table(
        'catch_up_solutions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('prediction_id', sa.Integer(), comment='关联的预测记录ID'),
        
        # 方案基本信息
        sa.Column('solution_name', sa.String(200), nullable=False, comment='方案名称'),
        sa.Column('solution_type', sa.String(50), comment='方案类型: manpower/overtime/process/hybrid'),
        sa.Column('description', sa.Text(), comment='方案描述'),
        
        # 方案详情和评估
        sa.Column('actions', sa.JSON(), comment='具体行动计划'),
        sa.Column('estimated_catch_up_days', sa.Integer(), comment='预计可追回天数'),
        sa.Column('additional_cost', sa.DECIMAL(12, 2), comment='额外成本'),
        sa.Column('risk_level', sa.String(20), comment='方案风险等级: low/medium/high'),
        sa.Column('success_rate', sa.DECIMAL(5, 2), comment='成功率 (0-1)'),
        sa.Column('evaluation_details', sa.JSON(), comment='评估详情'),
        
        # 方案状态
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='状态: pending/approved/rejected/implementing/completed/cancelled'),
        sa.Column('is_recommended', sa.Boolean(), nullable=False, server_default=sa.text('0'), comment='是否为推荐方案'),
        
        # 审批信息
        sa.Column('approved_by', sa.Integer(), comment='审批人ID'),
        sa.Column('approved_at', sa.DateTime(), comment='审批时间'),
        sa.Column('approval_comment', sa.Text(), comment='审批意见'),
        
        # 实施信息
        sa.Column('implementation_started_at', sa.DateTime(), comment='开始实施时间'),
        sa.Column('implementation_completed_at', sa.DateTime(), comment='完成实施时间'),
        sa.Column('actual_catch_up_days', sa.Integer(), comment='实际追回天数'),
        sa.Column('actual_cost', sa.DECIMAL(12, 2), comment='实际成本'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        
        sa.ForeignKeyConstraint(['prediction_id'], ['project_schedule_prediction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='赶工方案表'
    )
    
    # 创建索引
    op.create_index('idx_project_solution', 'catch_up_solutions', ['project_id'])
    op.create_index('idx_prediction', 'catch_up_solutions', ['prediction_id'])
    op.create_index('idx_project_status', 'catch_up_solutions', ['project_id', 'status'])
    op.create_index('idx_solution_type', 'catch_up_solutions', ['solution_type'])
    
    # ==================== 进度预警记录表 ====================
    op.create_table(
        'schedule_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('prediction_id', sa.Integer(), comment='关联的预测记录ID'),
        
        # 预警信息
        sa.Column('alert_type', sa.String(50), nullable=False, comment='预警类型: delay_warning/velocity_drop/milestone_risk/critical_path'),
        sa.Column('severity', sa.String(20), nullable=False, comment='严重程度: low/medium/high/critical'),
        sa.Column('title', sa.String(200), nullable=False, comment='预警标题'),
        sa.Column('message', sa.Text(), nullable=False, comment='预警消息'),
        
        # 预警详情
        sa.Column('alert_details', sa.JSON(), comment='预警详细信息'),
        
        # 通知信息
        sa.Column('notified_users', sa.JSON(), comment='已通知用户列表'),
        sa.Column('notification_channels', sa.JSON(), comment='通知渠道'),
        
        # 预警状态
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('0'), comment='是否已读'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default=sa.text('0'), comment='是否已解决'),
        
        # 确认信息
        sa.Column('acknowledged_by', sa.Integer(), comment='确认人ID'),
        sa.Column('acknowledged_at', sa.DateTime(), comment='确认时间'),
        sa.Column('acknowledgement_comment', sa.Text(), comment='确认备注'),
        
        # 解决信息
        sa.Column('resolved_by', sa.Integer(), comment='解决人ID'),
        sa.Column('resolved_at', sa.DateTime(), comment='解决时间'),
        sa.Column('resolution_comment', sa.Text(), comment='解决说明'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        
        sa.ForeignKeyConstraint(['prediction_id'], ['project_schedule_prediction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='进度预警记录表'
    )
    
    # 创建索引
    op.create_index('idx_project_alert', 'schedule_alerts', ['project_id'])
    op.create_index('idx_prediction_alert', 'schedule_alerts', ['prediction_id'])
    op.create_index('idx_project_severity', 'schedule_alerts', ['project_id', 'severity'])
    op.create_index('idx_alert_type', 'schedule_alerts', ['alert_type'])
    op.create_index('idx_is_read', 'schedule_alerts', ['is_read'])
    op.create_index('idx_is_resolved', 'schedule_alerts', ['is_resolved'])
    op.create_index('idx_alert_created_at', 'schedule_alerts', ['created_at'])
    
    print("✅ 进度偏差预警系统数据表创建完成")
    print("   - project_schedule_prediction (进度预测表)")
    print("   - catch_up_solutions (赶工方案表)")
    print("   - schedule_alerts (预警记录表)")


def downgrade():
    """降级数据库：删除进度预测系统相关表"""
    op.drop_table('schedule_alerts')
    op.drop_table('catch_up_solutions')
    op.drop_table('project_schedule_prediction')
    
    print("⚠️  进度偏差预警系统数据表已删除")
