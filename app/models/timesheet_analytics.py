# -*- coding: utf-8 -*-
"""
工时分析与预测模块 ORM 模型
包含：工时分析汇总、工时预测、工时趋势
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


# ==================== 枚举定义 ====================

class AnalyticsPeriodEnum(str, Enum):
    """分析周期"""
    DAILY = 'DAILY'          # 日度
    WEEKLY = 'WEEKLY'        # 周度
    MONTHLY = 'MONTHLY'      # 月度
    QUARTERLY = 'QUARTERLY'  # 季度
    YEARLY = 'YEARLY'        # 年度


class AnalyticsDimensionEnum(str, Enum):
    """分析维度"""
    USER = 'USER'            # 人员
    PROJECT = 'PROJECT'      # 项目
    DEPARTMENT = 'DEPARTMENT'  # 部门
    TASK = 'TASK'            # 任务
    OVERTIME = 'OVERTIME'    # 加班
    EFFICIENCY = 'EFFICIENCY'  # 效率


class ForecastMethodEnum(str, Enum):
    """预测方法"""
    HISTORICAL_AVERAGE = 'HISTORICAL_AVERAGE'  # 历史平均法
    LINEAR_REGRESSION = 'LINEAR_REGRESSION'    # 线性回归
    TREND_FORECAST = 'TREND_FORECAST'          # 趋势预测


class AlertLevelEnum(str, Enum):
    """预警级别"""
    LOW = 'LOW'              # 低
    MEDIUM = 'MEDIUM'        # 中
    HIGH = 'HIGH'            # 高
    CRITICAL = 'CRITICAL'    # 严重


# ==================== 工时分析汇总 ====================

class TimesheetAnalytics(Base, TimestampMixin):
    """工时分析汇总表"""
    __tablename__ = 'timesheet_analytics'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 分析维度
    period_type = Column(String(20), nullable=False, comment='周期类型')
    dimension = Column(String(20), nullable=False, comment='分析维度')

    # 时间范围
    start_date = Column(Date, nullable=False, comment='开始日期')
    end_date = Column(Date, nullable=False, comment='结束日期')
    year = Column(Integer, comment='年份')
    quarter = Column(Integer, comment='季度')
    month = Column(Integer, comment='月份')
    week = Column(Integer, comment='周数')

    # 关联维度
    user_id = Column(Integer, ForeignKey('users.id'), comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    project_name = Column(String(200), comment='项目名称')
    department_id = Column(Integer, comment='部门ID')
    department_name = Column(String(100), comment='部门名称')

    # 工时统计
    total_hours = Column(Numeric(10, 2), default=0, comment='总工时')
    normal_hours = Column(Numeric(10, 2), default=0, comment='正常工时')
    overtime_hours = Column(Numeric(10, 2), default=0, comment='加班工时')
    weekend_hours = Column(Numeric(10, 2), default=0, comment='周末工时')
    holiday_hours = Column(Numeric(10, 2), default=0, comment='节假日工时')

    # 计划与实际对比
    planned_hours = Column(Numeric(10, 2), comment='计划工时')
    actual_hours = Column(Numeric(10, 2), comment='实际工时')
    variance_hours = Column(Numeric(10, 2), comment='差异工时')
    variance_rate = Column(Numeric(5, 2), comment='差异率(%)')

    # 效率指标
    efficiency_rate = Column(Numeric(5, 2), comment='效率率(实际/计划*100)')
    utilization_rate = Column(Numeric(5, 2), comment='利用率(%)')
    overtime_rate = Column(Numeric(5, 2), comment='加班率(%)')

    # 负荷指标
    workload_saturation = Column(Numeric(5, 2), comment='工时饱和度(%)')
    standard_hours = Column(Numeric(10, 2), comment='标准工时')
    workload_level = Column(String(20), comment='负荷等级(LOW/MEDIUM/HIGH/OVERLOAD)')

    # 统计数量
    entries_count = Column(Integer, default=0, comment='工时记录数')
    projects_count = Column(Integer, default=0, comment='参与项目数')
    tasks_count = Column(Integer, default=0, comment='任务数')
    users_count = Column(Integer, default=0, comment='人员数')

    # 分布数据（用于可视化）
    daily_distribution = Column(JSON, comment='每日分布(折线图)')
    project_distribution = Column(JSON, comment='项目分布(饼图)')
    department_distribution = Column(JSON, comment='部门分布(柱状图)')
    overtime_distribution = Column(JSON, comment='加班分布')
    efficiency_trend = Column(JSON, comment='效率趋势')

    # 排名
    rank_in_department = Column(Integer, comment='部门排名')
    rank_in_company = Column(Integer, comment='公司排名')

    # 备注
    notes = Column(Text, comment='备注')
    
    # 快照时间
    snapshot_at = Column(DateTime, default=datetime.now, comment='快照时间')

    __table_args__ = (
        Index('idx_analytics_period', 'period_type', 'start_date', 'end_date'),
        Index('idx_analytics_user', 'user_id', 'period_type'),
        Index('idx_analytics_project', 'project_id', 'period_type'),
        Index('idx_analytics_dept', 'department_id', 'period_type'),
        Index('idx_analytics_dimension', 'dimension', 'period_type'),
        Index('idx_analytics_date_range', 'start_date', 'end_date'),
        {'comment': '工时分析汇总表'}
    )


# ==================== 工时趋势 ====================

class TimesheetTrend(Base, TimestampMixin):
    """工时趋势表"""
    __tablename__ = 'timesheet_trend'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 趋势维度
    trend_type = Column(String(20), nullable=False, comment='趋势类型(USER/PROJECT/DEPT/COMPANY)')
    period_type = Column(String(20), nullable=False, comment='周期类型')

    # 关联对象
    user_id = Column(Integer, ForeignKey('users.id'), comment='用户ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    department_id = Column(Integer, comment='部门ID')

    # 时间点
    trend_date = Column(Date, nullable=False, comment='趋势日期')
    year = Column(Integer, comment='年份')
    quarter = Column(Integer, comment='季度')
    month = Column(Integer, comment='月份')
    week = Column(Integer, comment='周数')

    # 工时数据
    total_hours = Column(Numeric(10, 2), default=0, comment='总工时')
    normal_hours = Column(Numeric(10, 2), default=0, comment='正常工时')
    overtime_hours = Column(Numeric(10, 2), default=0, comment='加班工时')

    # 趋势指标
    hours_change = Column(Numeric(10, 2), comment='工时变化量')
    hours_change_rate = Column(Numeric(5, 2), comment='工时变化率(%)')
    moving_average_7d = Column(Numeric(10, 2), comment='7日移动平均')
    moving_average_30d = Column(Numeric(10, 2), comment='30日移动平均')

    # 效率趋势
    efficiency_rate = Column(Numeric(5, 2), comment='效率率')
    efficiency_change = Column(Numeric(5, 2), comment='效率变化')
    
    # 负荷趋势
    workload_saturation = Column(Numeric(5, 2), comment='工时饱和度')
    workload_trend = Column(String(20), comment='负荷趋势(INCREASING/STABLE/DECREASING)')

    # 排名趋势
    rank = Column(Integer, comment='排名')
    rank_change = Column(Integer, comment='排名变化')

    __table_args__ = (
        Index('idx_trend_type_date', 'trend_type', 'trend_date'),
        Index('idx_trend_user', 'user_id', 'trend_date'),
        Index('idx_trend_project', 'project_id', 'trend_date'),
        Index('idx_trend_dept', 'department_id', 'trend_date'),
        Index('idx_trend_period', 'period_type', 'trend_date'),
        {'comment': '工时趋势表'}
    )


# ==================== 工时预测 ====================

class TimesheetForecast(Base, TimestampMixin):
    """工时预测表"""
    __tablename__ = 'timesheet_forecast'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    forecast_no = Column(String(50), unique=True, comment='预测编号')

    # 预测类型
    forecast_type = Column(String(20), nullable=False, comment='预测类型(PROJECT/COMPLETION/WORKLOAD/GAP)')
    forecast_method = Column(String(30), nullable=False, comment='预测方法')

    # 关联对象
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    project_name = Column(String(200), comment='项目名称')
    user_id = Column(Integer, ForeignKey('users.id'), comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    department_id = Column(Integer, comment='部门ID')

    # 预测时间
    forecast_date = Column(Date, nullable=False, comment='预测日期')
    target_date = Column(Date, comment='目标日期')
    forecast_period_days = Column(Integer, comment='预测周期(天)')

    # 历史数据基础
    historical_start_date = Column(Date, comment='历史数据起始日期')
    historical_end_date = Column(Date, comment='历史数据截止日期')
    historical_hours = Column(Numeric(10, 2), comment='历史总工时')
    historical_projects_count = Column(Integer, comment='参考项目数')

    # 预测结果
    predicted_hours = Column(Numeric(10, 2), nullable=False, comment='预测工时')
    predicted_hours_min = Column(Numeric(10, 2), comment='预测工时最小值')
    predicted_hours_max = Column(Numeric(10, 2), comment='预测工时最大值')
    confidence_level = Column(Numeric(5, 2), comment='置信度(%)')

    # 完工时间预测
    predicted_completion_date = Column(Date, comment='预测完工日期')
    predicted_days_remaining = Column(Integer, comment='预测剩余天数')

    # 当前状态
    current_progress = Column(Numeric(5, 2), comment='当前进度(%)')
    current_consumed_hours = Column(Numeric(10, 2), comment='当前已消耗工时')
    remaining_hours = Column(Numeric(10, 2), comment='剩余工时')

    # 缺口分析
    required_hours = Column(Numeric(10, 2), comment='需求工时')
    available_hours = Column(Numeric(10, 2), comment='可用工时')
    gap_hours = Column(Numeric(10, 2), comment='缺口工时')
    gap_rate = Column(Numeric(5, 2), comment='缺口率(%)')

    # 负荷预警
    workload_saturation = Column(Numeric(5, 2), comment='工时饱和度预测')
    alert_level = Column(String(20), comment='预警级别')
    alert_message = Column(Text, comment='预警信息')

    # 算法参数
    algorithm_params = Column(JSON, comment='算法参数')
    feature_importance = Column(JSON, comment='特征重要性')

    # 模型评估
    model_accuracy = Column(Numeric(5, 2), comment='模型准确度(%)')
    model_error_rate = Column(Numeric(5, 2), comment='模型误差率(%)')
    r_squared = Column(Numeric(5, 4), comment='R²决定系数')

    # 相似项目（历史平均法）
    similar_projects = Column(JSON, comment='相似项目列表')
    similarity_score = Column(Numeric(5, 2), comment='相似度评分')

    # 趋势数据
    trend_data = Column(JSON, comment='趋势数据(用于可视化)')
    forecast_curve = Column(JSON, comment='预测曲线数据')

    # 建议
    recommendations = Column(JSON, comment='建议措施')

    # 验证
    is_validated = Column(Integer, default=0, comment='是否已验证')
    actual_hours = Column(Numeric(10, 2), comment='实际工时(用于验证)')
    actual_completion_date = Column(Date, comment='实际完工日期')
    prediction_error = Column(Numeric(10, 2), comment='预测误差')

    # 备注
    notes = Column(Text, comment='备注')

    __table_args__ = (
        Index('idx_forecast_type', 'forecast_type', 'forecast_date'),
        Index('idx_ts_forecast_project', 'project_id', 'forecast_date'),
        Index('idx_forecast_user', 'user_id', 'forecast_date'),
        Index('idx_forecast_method', 'forecast_method'),
        Index('idx_forecast_alert', 'alert_level', 'forecast_date'),
        {'comment': '工时预测表'}
    )


# ==================== 工时异常记录 ====================

class TimesheetAnomaly(Base, TimestampMixin):
    """工时异常记录表"""
    __tablename__ = 'timesheet_anomaly'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 异常类型
    anomaly_type = Column(String(30), nullable=False, comment='异常类型(OVERLOAD/UNDERLOAD/SPIKE/MISSING)')
    severity = Column(String(20), comment='严重程度')

    # 关联对象
    user_id = Column(Integer, ForeignKey('users.id'), comment='用户ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    department_id = Column(Integer, comment='部门ID')
    timesheet_id = Column(Integer, ForeignKey('timesheet.id'), comment='工时记录ID')

    # 时间
    detected_date = Column(Date, nullable=False, comment='检测日期')
    anomaly_date = Column(Date, comment='异常日期')

    # 异常值
    expected_value = Column(Numeric(10, 2), comment='期望值')
    actual_value = Column(Numeric(10, 2), comment='实际值')
    deviation = Column(Numeric(10, 2), comment='偏差')
    deviation_rate = Column(Numeric(5, 2), comment='偏差率(%)')

    # 描述
    description = Column(Text, comment='异常描述')
    
    # 处理
    is_resolved = Column(Integer, default=0, comment='是否已处理')
    resolved_at = Column(DateTime, comment='处理时间')
    resolved_by = Column(Integer, ForeignKey('users.id'), comment='处理人')
    resolution_notes = Column(Text, comment='处理说明')

    __table_args__ = (
        Index('idx_ts_anomaly_type', 'anomaly_type', 'detected_date'),
        Index('idx_ts_anomaly_user', 'user_id', 'detected_date'),
        Index('idx_ts_anomaly_resolved', 'is_resolved'),
        {'comment': '工时异常记录表'}
    )
