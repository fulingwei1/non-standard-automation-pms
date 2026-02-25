# -*- coding: utf-8 -*-
"""
工时管理模块 ORM 模型
包含：工时记录、工时审批、工时汇总、加班申请
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
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

class TimesheetStatusEnum(str, Enum):
    """工时状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    APPROVED = 'APPROVED'    # 已通过
    REJECTED = 'REJECTED'    # 已驳回
    CANCELLED = 'CANCELLED'  # 已取消


class OvertimeTypeEnum(str, Enum):
    """加班类型"""
    NORMAL = 'NORMAL'        # 正常工时
    OVERTIME = 'OVERTIME'    # 加班
    WEEKEND = 'WEEKEND'      # 周末加班
    HOLIDAY = 'HOLIDAY'      # 节假日加班


# ==================== 工时记录 ====================

class Timesheet(Base, TimestampMixin):
    """工时记录"""
    __tablename__ = 'timesheet'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    timesheet_no = Column(String(50), comment='工时单号')

    # 人员信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    department_id = Column(Integer, comment='部门ID')
    department_name = Column(String(100), comment='部门名称')

    # 项目任务关联
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID（非标项目）')
    project_code = Column(String(50), comment='项目编号')
    project_name = Column(String(200), comment='项目名称')
    rd_project_id = Column(Integer, ForeignKey('rd_project.id'), nullable=True, comment='研发项目ID（可选，如果填写则直接关联研发项目）')
    task_id = Column(Integer, comment='任务ID')
    task_name = Column(String(200), comment='任务名称')
    assign_id = Column(Integer, comment='任务分配ID')

    # 工时信息
    work_date = Column(Date, nullable=False, comment='工作日期')
    hours = Column(Numeric(5, 2), nullable=False, comment='工时(小时)')
    overtime_type = Column(String(20), default='NORMAL', comment='加班类型')

    # 工作内容
    work_content = Column(Text, comment='工作内容')
    work_result = Column(Text, comment='工作成果')

    # 进度更新
    progress_before = Column(Integer, comment='更新前进度(%)')
    progress_after = Column(Integer, comment='更新后进度(%)')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 提交时间
    submit_time = Column(DateTime, comment='提交时间')

    # 审核信息
    approver_id = Column(Integer, ForeignKey('users.id'), comment='审核人ID')
    approver_name = Column(String(50), comment='审核人')
    approve_time = Column(DateTime, comment='审核时间')
    approve_comment = Column(Text, comment='审核意见')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    rd_project = relationship('RdProject', foreign_keys=[rd_project_id])

    __table_args__ = (
        Index('idx_ts_user', 'user_id'),
        Index('idx_ts_project', 'project_id'),
        Index('idx_ts_rd_project', 'rd_project_id'),
        Index('idx_ts_date', 'work_date'),
        Index('idx_ts_status', 'status'),
        Index('idx_ts_user_date', 'user_id', 'work_date'),
        {'comment': '工时记录表'}
    )


# ==================== 工时批次（周工时表） ====================

class TimesheetBatch(Base, TimestampMixin):
    """工时批次（周工时表）"""
    __tablename__ = 'timesheet_batch'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    batch_no = Column(String(50), unique=True, nullable=False, comment='批次编号')

    # 人员信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    department_id = Column(Integer, comment='部门ID')

    # 周期
    week_start = Column(Date, nullable=False, comment='周开始日期')
    week_end = Column(Date, nullable=False, comment='周结束日期')
    year = Column(Integer, comment='年份')
    week_number = Column(Integer, comment='周数')

    # 汇总
    total_hours = Column(Numeric(6, 2), default=0, comment='总工时')
    normal_hours = Column(Numeric(6, 2), default=0, comment='正常工时')
    overtime_hours = Column(Numeric(6, 2), default=0, comment='加班工时')
    entries_count = Column(Integer, default=0, comment='记录条数')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 提交
    submit_time = Column(DateTime, comment='提交时间')

    # 审批
    approver_id = Column(Integer, ForeignKey('users.id'), comment='审核人ID')
    approver_name = Column(String(50), comment='审核人')
    approve_time = Column(DateTime, comment='审核时间')
    approve_comment = Column(Text, comment='审核意见')

    __table_args__ = (
        Index('idx_batch_user', 'user_id'),
        Index('idx_batch_week', 'week_start', 'week_end'),
        Index('idx_batch_status', 'status'),
        Index('idx_batch_user_week', 'user_id', 'week_start', unique=True),
        {'comment': '工时批次表'}
    )


# ==================== 工时汇总 ====================

class TimesheetSummary(Base, TimestampMixin):
    """工时汇总（月度/项目）"""
    __tablename__ = 'timesheet_summary'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 汇总维度
    summary_type = Column(String(20), nullable=False, comment='汇总类型:USER_MONTH/PROJECT_MONTH/DEPT_MONTH')
    user_id = Column(Integer, ForeignKey('users.id'), comment='用户ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    department_id = Column(Integer, comment='部门ID')

    # 时间周期
    year = Column(Integer, nullable=False, comment='年份')
    month = Column(Integer, nullable=False, comment='月份')

    # 汇总数据
    total_hours = Column(Numeric(8, 2), default=0, comment='总工时')
    normal_hours = Column(Numeric(8, 2), default=0, comment='正常工时')
    overtime_hours = Column(Numeric(8, 2), default=0, comment='加班工时')
    weekend_hours = Column(Numeric(8, 2), default=0, comment='周末工时')
    holiday_hours = Column(Numeric(8, 2), default=0, comment='节假日工时')

    # 标准工时
    standard_hours = Column(Numeric(8, 2), comment='标准工时')
    work_days = Column(Integer, comment='工作日数')

    # 统计
    entries_count = Column(Integer, default=0, comment='记录条数')
    projects_count = Column(Integer, default=0, comment='参与项目数')

    # 分布明细
    project_breakdown = Column(JSON, comment='项目分布(JSON)')
    daily_breakdown = Column(JSON, comment='每日分布(JSON)')
    task_breakdown = Column(JSON, comment='任务分布(JSON)')

    # 审核状态分布
    status_breakdown = Column(JSON, comment='状态分布(JSON)')

    __table_args__ = (
        Index('idx_summary_user_month', 'user_id', 'year', 'month'),
        Index('idx_summary_project_month', 'project_id', 'year', 'month'),
        Index('idx_summary_dept_month', 'department_id', 'year', 'month'),
        {'comment': '工时汇总表'}
    )


# ==================== 加班申请 ====================

class OvertimeApplication(Base, TimestampMixin):
    """加班申请
    
    【状态】未启用 - 加班申请"""
    __tablename__ = 'overtime_application'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    application_no = Column(String(50), unique=True, nullable=False, comment='申请编号')

    # 申请人
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申请人ID')
    applicant_name = Column(String(50), comment='申请人姓名')
    department_id = Column(Integer, comment='部门ID')

    # 加班信息
    overtime_type = Column(String(20), nullable=False, comment='加班类型')
    overtime_date = Column(Date, nullable=False, comment='加班日期')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    planned_hours = Column(Numeric(5, 2), nullable=False, comment='计划加班时长')

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    project_name = Column(String(200), comment='项目名称')

    # 加班原因
    reason = Column(Text, nullable=False, comment='加班原因')
    work_content = Column(Text, comment='加班内容')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    # 审批
    approver_id = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approver_name = Column(String(50), comment='审批人')
    approve_time = Column(DateTime, comment='审批时间')
    approve_comment = Column(Text, comment='审批意见')

    # 实际加班
    actual_hours = Column(Numeric(5, 2), comment='实际加班时长')

    __table_args__ = (
        Index('idx_overtime_applicant', 'applicant_id'),
        Index('idx_overtime_date', 'overtime_date'),
        Index('idx_overtime_status', 'status'),
        {'comment': '加班申请表'}
    )


# ==================== 工时审批记录 ====================

class TimesheetApprovalLog(Base):
    """工时审批记录
    
    【状态】未启用 - 工时审批日志"""
    __tablename__ = 'timesheet_approval_log'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 关联
    timesheet_id = Column(Integer, ForeignKey('timesheet.id'), comment='工时记录ID')
    batch_id = Column(Integer, ForeignKey('timesheet_batch.id'), comment='工时批次ID')

    # 审批人
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='审批人ID')
    approver_name = Column(String(50), comment='审批人')

    # 审批动作
    action = Column(String(20), nullable=False, comment='审批动作')
    comment = Column(Text, comment='审批意见')

    # 审批时间
    approved_at = Column(DateTime, default=datetime.now, comment='审批时间')

    __table_args__ = (
        Index('idx_approval_timesheet', 'timesheet_id'),
        Index('idx_approval_batch', 'batch_id'),
        Index('idx_timesheet_approval_approver', 'approver_id'),
        {'comment': '工时审批记录表'}
    )


# ==================== 工时填报规则 ====================

class TimesheetRule(Base, TimestampMixin):
    """工时填报规则
    
    【状态】未启用 - 工时规则"""
    __tablename__ = 'timesheet_rule'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_code = Column(String(50), unique=True, nullable=False, comment='规则编码')
    rule_name = Column(String(100), nullable=False, comment='规则名称')

    # 适用范围
    apply_to_depts = Column(JSON, comment='适用部门')
    apply_to_roles = Column(JSON, comment='适用角色')

    # 规则参数
    standard_daily_hours = Column(Numeric(4, 2), default=8, comment='标准日工时')
    max_daily_hours = Column(Numeric(4, 2), default=12, comment='每日最大工时')
    min_entry_hours = Column(Numeric(4, 2), default=0.5, comment='最小记录单位')

    # 提交规则
    submit_deadline_day = Column(Integer, default=1, comment='提交截止日(下周几)')
    allow_backfill_days = Column(Integer, default=7, comment='允许补录天数')
    require_approval = Column(Boolean, default=True, comment='是否需要审批')

    # 提醒规则
    remind_unfilled = Column(Boolean, default=True, comment='未填报提醒')
    remind_time = Column(String(10), default='09:00', comment='提醒时间')

    is_active = Column(Boolean, default=True, comment='是否启用')

    __table_args__ = (
        Index('idx_rule_code', 'rule_code'),
        {'comment': '工时填报规则表'}
    )
