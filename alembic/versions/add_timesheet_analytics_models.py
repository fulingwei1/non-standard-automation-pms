"""Add timesheet analytics models

Revision ID: timesheet_analytics_v1
Revises: 
Create Date: 2024-01-15 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'timesheet_analytics_v1'
down_revision = None  # 根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    # 创建工时分析汇总表
    op.create_table(
        'timesheet_analytics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('period_type', sa.String(20), nullable=False, comment='周期类型'),
        sa.Column('dimension', sa.String(20), nullable=False, comment='分析维度'),
        sa.Column('start_date', sa.Date(), nullable=False, comment='开始日期'),
        sa.Column('end_date', sa.Date(), nullable=False, comment='结束日期'),
        sa.Column('year', sa.Integer(), comment='年份'),
        sa.Column('quarter', sa.Integer(), comment='季度'),
        sa.Column('month', sa.Integer(), comment='月份'),
        sa.Column('week', sa.Integer(), comment='周数'),
        
        sa.Column('user_id', sa.Integer(), comment='用户ID'),
        sa.Column('user_name', sa.String(50), comment='用户姓名'),
        sa.Column('project_id', sa.Integer(), comment='项目ID'),
        sa.Column('project_name', sa.String(200), comment='项目名称'),
        sa.Column('department_id', sa.Integer(), comment='部门ID'),
        sa.Column('department_name', sa.String(100), comment='部门名称'),
        
        sa.Column('total_hours', sa.Numeric(10, 2), default=0, comment='总工时'),
        sa.Column('normal_hours', sa.Numeric(10, 2), default=0, comment='正常工时'),
        sa.Column('overtime_hours', sa.Numeric(10, 2), default=0, comment='加班工时'),
        sa.Column('weekend_hours', sa.Numeric(10, 2), default=0, comment='周末工时'),
        sa.Column('holiday_hours', sa.Numeric(10, 2), default=0, comment='节假日工时'),
        
        sa.Column('planned_hours', sa.Numeric(10, 2), comment='计划工时'),
        sa.Column('actual_hours', sa.Numeric(10, 2), comment='实际工时'),
        sa.Column('variance_hours', sa.Numeric(10, 2), comment='差异工时'),
        sa.Column('variance_rate', sa.Numeric(5, 2), comment='差异率(%)'),
        
        sa.Column('efficiency_rate', sa.Numeric(5, 2), comment='效率率(%)'),
        sa.Column('utilization_rate', sa.Numeric(5, 2), comment='利用率(%)'),
        sa.Column('overtime_rate', sa.Numeric(5, 2), comment='加班率(%)'),
        sa.Column('workload_saturation', sa.Numeric(5, 2), comment='工时饱和度(%)'),
        sa.Column('standard_hours', sa.Numeric(10, 2), comment='标准工时'),
        sa.Column('workload_level', sa.String(20), comment='负荷等级'),
        
        sa.Column('entries_count', sa.Integer(), default=0, comment='工时记录数'),
        sa.Column('projects_count', sa.Integer(), default=0, comment='参与项目数'),
        sa.Column('tasks_count', sa.Integer(), default=0, comment='任务数'),
        sa.Column('users_count', sa.Integer(), default=0, comment='人员数'),
        
        sa.Column('daily_distribution', sa.JSON(), comment='每日分布'),
        sa.Column('project_distribution', sa.JSON(), comment='项目分布'),
        sa.Column('department_distribution', sa.JSON(), comment='部门分布'),
        sa.Column('overtime_distribution', sa.JSON(), comment='加班分布'),
        sa.Column('efficiency_trend', sa.JSON(), comment='效率趋势'),
        
        sa.Column('rank_in_department', sa.Integer(), comment='部门排名'),
        sa.Column('rank_in_company', sa.Integer(), comment='公司排名'),
        sa.Column('notes', sa.Text(), comment='备注'),
        sa.Column('snapshot_at', sa.DateTime(), comment='快照时间'),
        
        sa.Column('created_at', sa.DateTime(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        comment='工时分析汇总表'
    )
    
    # 创建索引
    op.create_index('idx_analytics_period', 'timesheet_analytics', ['period_type', 'start_date', 'end_date'])
    op.create_index('idx_analytics_user', 'timesheet_analytics', ['user_id', 'period_type'])
    op.create_index('idx_analytics_project', 'timesheet_analytics', ['project_id', 'period_type'])
    op.create_index('idx_analytics_dept', 'timesheet_analytics', ['department_id', 'period_type'])
    op.create_index('idx_analytics_dimension', 'timesheet_analytics', ['dimension', 'period_type'])
    
    # 创建工时趋势表
    op.create_table(
        'timesheet_trend',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('trend_type', sa.String(20), nullable=False, comment='趋势类型'),
        sa.Column('period_type', sa.String(20), nullable=False, comment='周期类型'),
        
        sa.Column('user_id', sa.Integer(), comment='用户ID'),
        sa.Column('project_id', sa.Integer(), comment='项目ID'),
        sa.Column('department_id', sa.Integer(), comment='部门ID'),
        
        sa.Column('trend_date', sa.Date(), nullable=False, comment='趋势日期'),
        sa.Column('year', sa.Integer(), comment='年份'),
        sa.Column('quarter', sa.Integer(), comment='季度'),
        sa.Column('month', sa.Integer(), comment='月份'),
        sa.Column('week', sa.Integer(), comment='周数'),
        
        sa.Column('total_hours', sa.Numeric(10, 2), default=0, comment='总工时'),
        sa.Column('normal_hours', sa.Numeric(10, 2), default=0, comment='正常工时'),
        sa.Column('overtime_hours', sa.Numeric(10, 2), default=0, comment='加班工时'),
        
        sa.Column('hours_change', sa.Numeric(10, 2), comment='工时变化量'),
        sa.Column('hours_change_rate', sa.Numeric(5, 2), comment='工时变化率(%)'),
        sa.Column('moving_average_7d', sa.Numeric(10, 2), comment='7日移动平均'),
        sa.Column('moving_average_30d', sa.Numeric(10, 2), comment='30日移动平均'),
        
        sa.Column('efficiency_rate', sa.Numeric(5, 2), comment='效率率'),
        sa.Column('efficiency_change', sa.Numeric(5, 2), comment='效率变化'),
        sa.Column('workload_saturation', sa.Numeric(5, 2), comment='工时饱和度'),
        sa.Column('workload_trend', sa.String(20), comment='负荷趋势'),
        
        sa.Column('rank', sa.Integer(), comment='排名'),
        sa.Column('rank_change', sa.Integer(), comment='排名变化'),
        
        sa.Column('created_at', sa.DateTime(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        comment='工时趋势表'
    )
    
    op.create_index('idx_trend_type_date', 'timesheet_trend', ['trend_type', 'trend_date'])
    op.create_index('idx_trend_user', 'timesheet_trend', ['user_id', 'trend_date'])
    op.create_index('idx_trend_project', 'timesheet_trend', ['project_id', 'trend_date'])
    
    # 创建工时预测表
    op.create_table(
        'timesheet_forecast',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('forecast_no', sa.String(50), unique=True, comment='预测编号'),
        sa.Column('forecast_type', sa.String(20), nullable=False, comment='预测类型'),
        sa.Column('forecast_method', sa.String(30), nullable=False, comment='预测方法'),
        
        sa.Column('project_id', sa.Integer(), comment='项目ID'),
        sa.Column('project_name', sa.String(200), comment='项目名称'),
        sa.Column('user_id', sa.Integer(), comment='用户ID'),
        sa.Column('user_name', sa.String(50), comment='用户姓名'),
        sa.Column('department_id', sa.Integer(), comment='部门ID'),
        
        sa.Column('forecast_date', sa.Date(), nullable=False, comment='预测日期'),
        sa.Column('target_date', sa.Date(), comment='目标日期'),
        sa.Column('forecast_period_days', sa.Integer(), comment='预测周期(天)'),
        
        sa.Column('historical_start_date', sa.Date(), comment='历史数据起始日期'),
        sa.Column('historical_end_date', sa.Date(), comment='历史数据截止日期'),
        sa.Column('historical_hours', sa.Numeric(10, 2), comment='历史总工时'),
        sa.Column('historical_projects_count', sa.Integer(), comment='参考项目数'),
        
        sa.Column('predicted_hours', sa.Numeric(10, 2), nullable=False, comment='预测工时'),
        sa.Column('predicted_hours_min', sa.Numeric(10, 2), comment='预测工时最小值'),
        sa.Column('predicted_hours_max', sa.Numeric(10, 2), comment='预测工时最大值'),
        sa.Column('confidence_level', sa.Numeric(5, 2), comment='置信度(%)'),
        
        sa.Column('predicted_completion_date', sa.Date(), comment='预测完工日期'),
        sa.Column('predicted_days_remaining', sa.Integer(), comment='预测剩余天数'),
        
        sa.Column('current_progress', sa.Numeric(5, 2), comment='当前进度(%)'),
        sa.Column('current_consumed_hours', sa.Numeric(10, 2), comment='当前已消耗工时'),
        sa.Column('remaining_hours', sa.Numeric(10, 2), comment='剩余工时'),
        
        sa.Column('required_hours', sa.Numeric(10, 2), comment='需求工时'),
        sa.Column('available_hours', sa.Numeric(10, 2), comment='可用工时'),
        sa.Column('gap_hours', sa.Numeric(10, 2), comment='缺口工时'),
        sa.Column('gap_rate', sa.Numeric(5, 2), comment='缺口率(%)'),
        
        sa.Column('workload_saturation', sa.Numeric(5, 2), comment='工时饱和度预测'),
        sa.Column('alert_level', sa.String(20), comment='预警级别'),
        sa.Column('alert_message', sa.Text(), comment='预警信息'),
        
        sa.Column('algorithm_params', sa.JSON(), comment='算法参数'),
        sa.Column('feature_importance', sa.JSON(), comment='特征重要性'),
        sa.Column('model_accuracy', sa.Numeric(5, 2), comment='模型准确度(%)'),
        sa.Column('model_error_rate', sa.Numeric(5, 2), comment='模型误差率(%)'),
        sa.Column('r_squared', sa.Numeric(5, 4), comment='R²决定系数'),
        
        sa.Column('similar_projects', sa.JSON(), comment='相似项目列表'),
        sa.Column('similarity_score', sa.Numeric(5, 2), comment='相似度评分'),
        sa.Column('trend_data', sa.JSON(), comment='趋势数据'),
        sa.Column('forecast_curve', sa.JSON(), comment='预测曲线数据'),
        sa.Column('recommendations', sa.JSON(), comment='建议措施'),
        
        sa.Column('is_validated', sa.Integer(), default=0, comment='是否已验证'),
        sa.Column('actual_hours', sa.Numeric(10, 2), comment='实际工时'),
        sa.Column('actual_completion_date', sa.Date(), comment='实际完工日期'),
        sa.Column('prediction_error', sa.Numeric(10, 2), comment='预测误差'),
        
        sa.Column('notes', sa.Text(), comment='备注'),
        sa.Column('created_at', sa.DateTime(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        comment='工时预测表'
    )
    
    op.create_index('idx_forecast_type', 'timesheet_forecast', ['forecast_type', 'forecast_date'])
    op.create_index('idx_forecast_project', 'timesheet_forecast', ['project_id', 'forecast_date'])
    op.create_index('idx_forecast_method', 'timesheet_forecast', ['forecast_method'])
    
    # 创建工时异常记录表
    op.create_table(
        'timesheet_anomaly',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('anomaly_type', sa.String(30), nullable=False, comment='异常类型'),
        sa.Column('severity', sa.String(20), comment='严重程度'),
        
        sa.Column('user_id', sa.Integer(), comment='用户ID'),
        sa.Column('project_id', sa.Integer(), comment='项目ID'),
        sa.Column('department_id', sa.Integer(), comment='部门ID'),
        sa.Column('timesheet_id', sa.Integer(), comment='工时记录ID'),
        
        sa.Column('detected_date', sa.Date(), nullable=False, comment='检测日期'),
        sa.Column('anomaly_date', sa.Date(), comment='异常日期'),
        
        sa.Column('expected_value', sa.Numeric(10, 2), comment='期望值'),
        sa.Column('actual_value', sa.Numeric(10, 2), comment='实际值'),
        sa.Column('deviation', sa.Numeric(10, 2), comment='偏差'),
        sa.Column('deviation_rate', sa.Numeric(5, 2), comment='偏差率(%)'),
        
        sa.Column('description', sa.Text(), comment='异常描述'),
        sa.Column('is_resolved', sa.Integer(), default=0, comment='是否已处理'),
        sa.Column('resolved_at', sa.DateTime(), comment='处理时间'),
        sa.Column('resolved_by', sa.Integer(), comment='处理人'),
        sa.Column('resolution_notes', sa.Text(), comment='处理说明'),
        
        sa.Column('created_at', sa.DateTime(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), comment='更新时间'),
        
        sa.PrimaryKeyConstraint('id'),
        comment='工时异常记录表'
    )
    
    op.create_index('idx_anomaly_type', 'timesheet_anomaly', ['anomaly_type', 'detected_date'])


def downgrade():
    op.drop_table('timesheet_anomaly')
    op.drop_table('timesheet_forecast')
    op.drop_table('timesheet_trend')
    op.drop_table('timesheet_analytics')
