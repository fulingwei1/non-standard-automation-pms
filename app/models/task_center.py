# -*- coding: utf-8 -*-
"""
个人任务中心模块 ORM 模型
包含：统一任务、岗位职责模板、任务日志、任务评论
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from enum import Enum


# ==================== 枚举定义 ====================

class TaskTypeEnum(str, Enum):
    """任务类型"""
    JOB_DUTY = 'JOB_DUTY'        # 岗位职责任务
    PROJECT_WBS = 'PROJECT_WBS'  # 项目WBS任务
    WORKFLOW = 'WORKFLOW'        # 流程待办任务
    TRANSFER = 'TRANSFER'        # 转办协作任务
    LEGACY = 'LEGACY'            # 遗留历史任务
    ALERT = 'ALERT'              # 预警跟踪任务
    PERSONAL = 'PERSONAL'        # 个人自建任务
    ASSIGNED = 'ASSIGNED'        # 临时指派任务


class TaskStatusEnum(str, Enum):
    """任务状态"""
    PENDING = 'PENDING'          # 待接收
    ACCEPTED = 'ACCEPTED'        # 已接收
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    PAUSED = 'PAUSED'            # 已暂停
    SUBMITTED = 'SUBMITTED'      # 已提交(待验收)
    APPROVED = 'APPROVED'        # 已通过
    REJECTED = 'REJECTED'        # 已驳回
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class TaskPriorityEnum(str, Enum):
    """任务优先级"""
    URGENT = 'URGENT'  # 紧急
    HIGH = 'HIGH'      # 高
    MEDIUM = 'MEDIUM'  # 中
    LOW = 'LOW'        # 低


class DutyFrequencyEnum(str, Enum):
    """职责频率"""
    DAILY = 'DAILY'          # 每日
    WEEKLY = 'WEEKLY'        # 每周
    BIWEEKLY = 'BIWEEKLY'    # 每两周
    MONTHLY = 'MONTHLY'      # 每月
    QUARTERLY = 'QUARTERLY'  # 每季度
    YEARLY = 'YEARLY'        # 每年


class CommentTypeEnum(str, Enum):
    """评论类型"""
    COMMENT = 'COMMENT'    # 普通评论
    PROGRESS = 'PROGRESS'  # 进度更新
    QUESTION = 'QUESTION'  # 提问
    REPLY = 'REPLY'        # 回复


# ==================== 统一任务表 ====================

class TaskUnified(Base, TimestampMixin):
    """统一任务表（聚合所有类型任务）"""
    __tablename__ = 'task_unified'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_code = Column(String(50), unique=True, nullable=False, comment='任务编号')
    
    # 任务基本信息
    title = Column(String(200), nullable=False, comment='任务标题')
    description = Column(Text, comment='任务描述')
    task_type = Column(String(20), nullable=False, comment='任务类型')
    
    # 来源追溯
    source_type = Column(String(50), comment='来源类型：PROJECT/WORKFLOW/MANUAL/SYSTEM')
    source_id = Column(Integer, comment='来源ID')
    source_name = Column(String(200), comment='来源名称')
    parent_task_id = Column(Integer, ForeignKey('task_unified.id'), comment='父任务ID')
    
    # 项目关联
    project_id = Column(Integer, ForeignKey('project.id'), comment='关联项目ID')
    project_code = Column(String(50), comment='项目编号')
    project_name = Column(String(200), comment='项目名称')
    wbs_code = Column(String(50), comment='WBS编码')
    
    # 人员分配
    assignee_id = Column(Integer, ForeignKey('user.id'), nullable=False, comment='执行人ID')
    assignee_name = Column(String(50), comment='执行人姓名')
    assigner_id = Column(Integer, ForeignKey('user.id'), comment='指派人ID')
    assigner_name = Column(String(50), comment='指派人姓名')
    
    # 时间信息
    plan_start_date = Column(Date, comment='计划开始日期')
    plan_end_date = Column(Date, comment='计划结束日期')
    actual_start_date = Column(Date, comment='实际开始日期')
    actual_end_date = Column(Date, comment='实际完成日期')
    deadline = Column(DateTime, comment='截止时间')
    
    # 工时信息
    estimated_hours = Column(Numeric(10, 2), comment='预估工时')
    actual_hours = Column(Numeric(10, 2), default=0, comment='实际工时')
    
    # 状态与进度
    status = Column(String(20), default='PENDING', comment='状态')
    progress = Column(Integer, default=0, comment='进度百分比')
    
    # 优先级与紧急度
    priority = Column(String(20), default='MEDIUM', comment='优先级')
    is_urgent = Column(Boolean, default=False, comment='是否紧急')
    
    # 周期性任务
    is_recurring = Column(Boolean, default=False, comment='是否周期性')
    recurrence_rule = Column(String(200), comment='周期规则(RRULE格式)')
    recurrence_end_date = Column(Date, comment='周期结束日期')
    
    # 转办信息
    is_transferred = Column(Boolean, default=False, comment='是否转办')
    transfer_from_id = Column(Integer, ForeignKey('user.id'), comment='转办来源人ID')
    transfer_from_name = Column(String(50), comment='转办来源人')
    transfer_reason = Column(Text, comment='转办原因')
    transfer_time = Column(DateTime, comment='转办时间')
    
    # 交付物
    deliverables = Column(JSON, comment='交付物清单')
    attachments = Column(JSON, comment='附件列表')
    
    # 标签与分类
    tags = Column(JSON, comment='标签')
    category = Column(String(50), comment='分类')
    
    # 提醒设置
    reminder_enabled = Column(Boolean, default=True, comment='是否开启提醒')
    reminder_before_hours = Column(Integer, default=24, comment='提前提醒小时数')
    
    # 审计字段
    created_by = Column(Integer, ForeignKey('user.id'), comment='创建人ID')
    updated_by = Column(Integer, ForeignKey('user.id'), comment='更新人ID')
    
    # 关系
    parent_task = relationship('TaskUnified', remote_side=[id], backref='sub_tasks')
    comments = relationship('TaskComment', back_populates='task')
    operation_logs = relationship('TaskOperationLog', back_populates='task')
    
    __table_args__ = (
        Index('idx_task_code', 'task_code'),
        Index('idx_task_assignee', 'assignee_id'),
        Index('idx_task_project', 'project_id'),
        Index('idx_task_status', 'status'),
        Index('idx_task_type', 'task_type'),
        Index('idx_task_deadline', 'deadline'),
        Index('idx_task_priority', 'priority'),
        {'comment': '统一任务表'}
    )


# ==================== 岗位职责模板 ====================

class JobDutyTemplate(Base, TimestampMixin):
    """岗位职责任务模板"""
    __tablename__ = 'job_duty_template'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    position_id = Column(Integer, nullable=False, comment='岗位ID')
    position_name = Column(String(100), comment='岗位名称')
    department_id = Column(Integer, comment='部门ID')
    
    duty_name = Column(String(200), nullable=False, comment='职责名称')
    duty_description = Column(Text, comment='职责描述')
    
    # 周期设置
    frequency = Column(String(20), nullable=False, comment='频率')
    day_of_week = Column(Integer, comment='周几(1-7)')
    day_of_month = Column(Integer, comment='几号(1-31)')
    month_of_year = Column(Integer, comment='几月(1-12)')
    
    # 任务生成规则
    auto_generate = Column(Boolean, default=True, comment='自动生成任务')
    generate_before_days = Column(Integer, default=3, comment='提前几天生成')
    deadline_offset_days = Column(Integer, default=0, comment='截止日期偏移')
    
    # 任务默认值
    default_priority = Column(String(20), default='MEDIUM', comment='默认优先级')
    estimated_hours = Column(Numeric(10, 2), comment='预估工时')
    
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    __table_args__ = (
        Index('idx_duty_position', 'position_id'),
        Index('idx_duty_frequency', 'frequency'),
        {'comment': '岗位职责任务模板表'}
    )


# ==================== 任务操作日志 ====================

class TaskOperationLog(Base):
    """任务操作日志"""
    __tablename__ = 'task_operation_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_id = Column(Integer, ForeignKey('task_unified.id'), nullable=False, comment='任务ID')
    operation_type = Column(String(50), nullable=False, comment='操作类型')
    operation_desc = Column(Text, comment='操作描述')
    old_value = Column(JSON, comment='变更前值')
    new_value = Column(JSON, comment='变更后值')
    operator_id = Column(Integer, ForeignKey('user.id'), comment='操作人ID')
    operator_name = Column(String(50), comment='操作人')
    operation_time = Column(DateTime, default=datetime.now, comment='操作时间')
    
    # 关系
    task = relationship('TaskUnified', back_populates='operation_logs')
    
    __table_args__ = (
        Index('idx_task_log_task', 'task_id'),
        Index('idx_task_log_operator', 'operator_id'),
        {'comment': '任务操作日志表'}
    )


# ==================== 任务评论 ====================

class TaskComment(Base):
    """任务评论与沟通"""
    __tablename__ = 'task_comment'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_id = Column(Integer, ForeignKey('task_unified.id'), nullable=False, comment='任务ID')
    content = Column(Text, nullable=False, comment='评论内容')
    comment_type = Column(String(20), default='COMMENT', comment='评论类型')
    parent_id = Column(Integer, ForeignKey('task_comment.id'), comment='回复的评论ID')
    commenter_id = Column(Integer, ForeignKey('user.id'), comment='评论人ID')
    commenter_name = Column(String(50), comment='评论人')
    mentioned_users = Column(JSON, comment='@的用户')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    task = relationship('TaskUnified', back_populates='comments')
    parent_comment = relationship('TaskComment', remote_side=[id], backref='replies')
    
    __table_args__ = (
        Index('idx_task_comment_task', 'task_id'),
        {'comment': '任务评论表'}
    )


# ==================== 任务提醒 ====================

class TaskReminder(Base, TimestampMixin):
    """任务提醒"""
    __tablename__ = 'task_reminder'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_id = Column(Integer, ForeignKey('task_unified.id'), nullable=False, comment='任务ID')
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, comment='用户ID')
    
    reminder_type = Column(String(20), nullable=False, comment='提醒类型:DEADLINE/OVERDUE/CUSTOM')
    remind_at = Column(DateTime, nullable=False, comment='提醒时间')
    is_sent = Column(Boolean, default=False, comment='是否已发送')
    sent_at = Column(DateTime, comment='发送时间')
    
    channel = Column(String(20), default='SYSTEM', comment='通知渠道:SYSTEM/EMAIL/WECHAT')
    
    __table_args__ = (
        Index('idx_reminder_task', 'task_id'),
        Index('idx_reminder_user', 'user_id'),
        Index('idx_reminder_time', 'remind_at'),
        {'comment': '任务提醒表'}
    )

