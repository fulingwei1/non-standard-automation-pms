# -*- coding: utf-8 -*-
"""
PMO 项目管理部模块 ORM 模型
包含：项目立项、阶段、里程碑、变更、风险、成本、会议、资源分配、结项
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text, Time
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin

# ==================== 枚举定义 ====================

class ProjectLevelEnum(str, Enum):
    """项目级别"""
    A = 'A'  # A级项目(重点)
    B = 'B'  # B级项目(一般)
    C = 'C'  # C级项目(简单)


class ProjectPhaseEnum(str, Enum):
    """项目阶段"""
    INITIATION = 'INITIATION'  # 立项阶段
    DESIGN = 'DESIGN'          # 设计阶段
    PRODUCTION = 'PRODUCTION'  # 生产阶段
    DELIVERY = 'DELIVERY'      # 交付阶段
    CLOSURE = 'CLOSURE'        # 结项阶段


class InitiationStatusEnum(str, Enum):
    """立项申请状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    REVIEWING = 'REVIEWING'  # 评审中
    APPROVED = 'APPROVED'    # 已批准
    REJECTED = 'REJECTED'    # 已驳回


class PhaseStatusEnum(str, Enum):
    """阶段状态"""
    PENDING = 'PENDING'        # 未开始
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    COMPLETED = 'COMPLETED'    # 已完成
    SKIPPED = 'SKIPPED'        # 已跳过


class MilestoneStatusEnum(str, Enum):
    """里程碑状态"""
    PENDING = 'PENDING'        # 待完成
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    COMPLETED = 'COMPLETED'    # 已完成
    DELAYED = 'DELAYED'        # 已延期
    CANCELLED = 'CANCELLED'    # 已取消


class ChangeTypeEnum(str, Enum):
    """变更类型"""
    SCOPE = 'SCOPE'          # 范围变更
    SCHEDULE = 'SCHEDULE'    # 进度变更
    COST = 'COST'            # 成本变更
    RESOURCE = 'RESOURCE'    # 资源变更
    REQUIREMENT = 'REQUIREMENT'  # 需求变更
    OTHER = 'OTHER'          # 其他变更


class ChangeLevelEnum(str, Enum):
    """变更级别"""
    MINOR = 'MINOR'      # 小变更
    MAJOR = 'MAJOR'      # 重大变更
    CRITICAL = 'CRITICAL'  # 关键变更


class ChangeStatusEnum(str, Enum):
    """变更状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    REVIEWING = 'REVIEWING'  # 评审中
    APPROVED = 'APPROVED'    # 已批准
    REJECTED = 'REJECTED'    # 已驳回
    CANCELLED = 'CANCELLED'  # 已取消


class RiskCategoryEnum(str, Enum):
    """风险类别"""
    TECHNICAL = 'TECHNICAL'  # 技术风险
    SCHEDULE = 'SCHEDULE'    # 进度风险
    COST = 'COST'            # 成本风险
    RESOURCE = 'RESOURCE'    # 资源风险
    EXTERNAL = 'EXTERNAL'    # 外部风险
    OTHER = 'OTHER'          # 其他风险


class RiskLevelEnum(str, Enum):
    """风险等级"""
    LOW = 'LOW'          # 低
    MEDIUM = 'MEDIUM'    # 中
    HIGH = 'HIGH'        # 高
    CRITICAL = 'CRITICAL'  # 严重


class RiskStatusEnum(str, Enum):
    """风险状态"""
    IDENTIFIED = 'IDENTIFIED'  # 已识别
    ANALYZING = 'ANALYZING'    # 分析中
    RESPONDING = 'RESPONDING'  # 应对中
    MONITORING = 'MONITORING'  # 监控中
    CLOSED = 'CLOSED'          # 已关闭


class MeetingTypeEnum(str, Enum):
    """会议类型"""
    KICKOFF = 'KICKOFF'              # 启动会
    WEEKLY = 'WEEKLY'                # 周例会
    MILESTONE_REVIEW = 'MILESTONE_REVIEW'  # 里程碑评审
    CHANGE_REVIEW = 'CHANGE_REVIEW'  # 变更评审
    RISK_REVIEW = 'RISK_REVIEW'      # 风险评审
    CLOSURE = 'CLOSURE'              # 结项会
    OTHER = 'OTHER'                  # 其他


class ResourceAllocationStatusEnum(str, Enum):
    """资源分配状态"""
    PLANNED = 'PLANNED'      # 已计划
    ACTIVE = 'ACTIVE'        # 生效中
    COMPLETED = 'COMPLETED'  # 已完成
    RELEASED = 'RELEASED'    # 已释放


# ==================== 项目立项 ====================

class PmoProjectInitiation(Base, TimestampMixin):
    """项目立项申请"""
    __tablename__ = 'pmo_project_initiation'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    application_no = Column(String(50), unique=True, nullable=False, comment='申请编号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID(审批通过后关联)')

    # 申请信息
    project_name = Column(String(200), nullable=False, comment='项目名称')
    project_type = Column(String(20), default='NEW', comment='项目类型:NEW/UPGRADE/MAINTAIN')
    project_level = Column(String(5), comment='建议级别:A/B/C')

    # 客户合同
    customer_name = Column(String(100), nullable=False, comment='客户名称')
    contract_no = Column(String(50), comment='合同编号')
    contract_amount = Column(Numeric(14, 2), comment='合同金额')

    # 时间要求
    required_start_date = Column(Date, comment='要求开始日期')
    required_end_date = Column(Date, comment='要求交付日期')

    # 技术信息
    technical_solution_id = Column(Integer, comment='关联技术方案ID')
    requirement_summary = Column(Text, comment='需求概述')
    technical_difficulty = Column(String(20), comment='技术难度:LOW/MEDIUM/HIGH')

    # 资源需求
    estimated_hours = Column(Integer, comment='预估工时')
    resource_requirements = Column(Text, comment='资源需求说明')

    # 风险评估
    risk_assessment = Column(Text, comment='初步风险评估')

    # 申请人
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申请人ID')
    applicant_name = Column(String(50), comment='申请人姓名')
    apply_time = Column(DateTime, default=datetime.now, comment='申请时间')

    # 审批状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 审批信息
    review_result = Column(Text, comment='评审结论')
    approved_pm_id = Column(Integer, ForeignKey('users.id'), comment='指定项目经理ID')
    approved_level = Column(String(5), comment='评定级别:A/B/C')
    approved_at = Column(DateTime, comment='审批时间')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')

    __table_args__ = (
        Index('idx_pmo_init_no', 'application_no'),
        Index('idx_pmo_init_status', 'status'),
        Index('idx_pmo_init_applicant', 'applicant_id'),
        {'comment': '项目立项申请表'}
    )


# ==================== 项目阶段 ====================

class PmoProjectPhase(Base, TimestampMixin):
    """项目阶段"""
    __tablename__ = 'pmo_project_phase'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 阶段信息
    phase_code = Column(String(20), nullable=False, comment='阶段编码')
    phase_name = Column(String(50), nullable=False, comment='阶段名称')
    phase_order = Column(Integer, default=0, comment='阶段顺序')

    # 时间
    plan_start_date = Column(Date, comment='计划开始')
    plan_end_date = Column(Date, comment='计划结束')
    actual_start_date = Column(Date, comment='实际开始')
    actual_end_date = Column(Date, comment='实际结束')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    progress = Column(Integer, default=0, comment='进度(%)')

    # 入口/出口条件
    entry_criteria = Column(Text, comment='入口条件')
    exit_criteria = Column(Text, comment='出口条件')
    entry_check_result = Column(Text, comment='入口检查结果')
    exit_check_result = Column(Text, comment='出口检查结果')

    # 评审
    review_required = Column(Boolean, default=True, comment='是否需要评审')
    review_date = Column(Date, comment='评审日期')
    review_result = Column(String(20), comment='评审结果:PASSED/CONDITIONAL/FAILED')
    review_notes = Column(Text, comment='评审记录')

    __table_args__ = (
        Index('idx_pmo_phase_project', 'project_id'),
        Index('idx_pmo_phase_code', 'phase_code'),
        {'comment': '项目阶段表'}
    )


# ==================== 项目变更 ====================

class PmoChangeRequest(Base, TimestampMixin):
    """项目变更申请"""
    __tablename__ = 'pmo_change_request'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    change_no = Column(String(50), unique=True, nullable=False, comment='变更编号')

    # 变更信息
    change_type = Column(String(20), nullable=False, comment='变更类型')
    change_level = Column(String(20), default='MINOR', comment='变更级别')
    title = Column(String(200), nullable=False, comment='变更标题')
    description = Column(Text, nullable=False, comment='变更描述')
    reason = Column(Text, comment='变更原因')

    # 影响评估
    schedule_impact = Column(Text, comment='进度影响')
    cost_impact = Column(Numeric(12, 2), comment='成本影响')
    quality_impact = Column(Text, comment='质量影响')
    resource_impact = Column(Text, comment='资源影响')

    # 申请人
    requestor_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申请人ID')
    requestor_name = Column(String(50), comment='申请人')
    request_time = Column(DateTime, default=datetime.now, comment='申请时间')

    # 审批状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 审批记录
    pm_approval = Column(Boolean, comment='项目经理审批')
    pm_approval_time = Column(DateTime, comment='项目经理审批时间')
    manager_approval = Column(Boolean, comment='部门经理审批')
    manager_approval_time = Column(DateTime, comment='部门经理审批时间')
    customer_approval = Column(Boolean, comment='客户确认')
    customer_approval_time = Column(DateTime, comment='客户确认时间')

    # 执行情况
    execution_status = Column(String(20), comment='执行状态:PENDING/EXECUTING/COMPLETED')
    execution_notes = Column(Text, comment='执行说明')
    completed_time = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('idx_pmo_change_project', 'project_id'),
        Index('idx_pmo_change_no', 'change_no'),
        Index('idx_pmo_change_status', 'status'),
        {'comment': '项目变更申请表'}
    )


# ==================== 项目风险 ====================

class PmoProjectRisk(Base, TimestampMixin):
    """项目风险"""
    __tablename__ = 'pmo_project_risk'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    risk_no = Column(String(50), unique=True, nullable=False, comment='风险编号')

    # 风险信息
    risk_category = Column(String(20), nullable=False, comment='风险类别')
    risk_name = Column(String(200), nullable=False, comment='风险名称')
    description = Column(Text, comment='风险描述')

    # 风险评估
    probability = Column(String(20), comment='发生概率:LOW/MEDIUM/HIGH')
    impact = Column(String(20), comment='影响程度:LOW/MEDIUM/HIGH')
    risk_level = Column(String(20), comment='风险等级:LOW/MEDIUM/HIGH/CRITICAL')

    # 应对措施
    response_strategy = Column(String(20), comment='应对策略:AVOID/MITIGATE/TRANSFER/ACCEPT')
    response_plan = Column(Text, comment='应对措施')

    # 责任人
    owner_id = Column(Integer, ForeignKey('users.id'), comment='责任人ID')
    owner_name = Column(String(50), comment='责任人')

    # 状态
    status = Column(String(20), default='IDENTIFIED', comment='状态')

    # 跟踪
    follow_up_date = Column(Date, comment='跟踪日期')
    last_update = Column(Text, comment='最新进展')

    # 触发/关闭
    trigger_condition = Column(Text, comment='触发条件')
    is_triggered = Column(Boolean, default=False, comment='是否已触发')
    triggered_date = Column(Date, comment='触发日期')
    closed_date = Column(Date, comment='关闭日期')
    closed_reason = Column(Text, comment='关闭原因')

    __table_args__ = (
        Index('idx_pmo_risk_project', 'project_id'),
        Index('idx_pmo_risk_level', 'risk_level'),
        Index('idx_pmo_risk_status', 'status'),
        {'comment': '项目风险表'}
    )


# ==================== 项目成本 ====================

class PmoProjectCost(Base, TimestampMixin):
    """项目成本"""
    __tablename__ = 'pmo_project_cost'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 成本类别
    cost_category = Column(String(50), nullable=False, comment='成本类别')
    cost_item = Column(String(100), nullable=False, comment='成本项')

    # 金额
    budget_amount = Column(Numeric(12, 2), default=0, comment='预算金额')
    actual_amount = Column(Numeric(12, 2), default=0, comment='实际金额')

    # 时间
    cost_month = Column(String(7), comment='成本月份(YYYY-MM)')
    record_date = Column(Date, comment='记录日期')

    # 来源
    source_type = Column(String(50), comment='来源类型')
    source_id = Column(Integer, comment='来源ID')
    source_no = Column(String(50), comment='来源单号')

    # 备注
    remarks = Column(Text, comment='备注')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    __table_args__ = (
        Index('idx_pmo_cost_project', 'project_id'),
        Index('idx_pmo_cost_category', 'cost_category'),
        Index('idx_pmo_cost_month', 'cost_month'),
        {'comment': '项目成本表'}
    )


# ==================== 项目会议 ====================

class PmoMeeting(Base, TimestampMixin):
    """项目会议"""
    __tablename__ = 'pmo_meeting'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID(可为空表示跨项目会议)')

    # 会议信息
    meeting_type = Column(String(20), nullable=False, comment='会议类型')
    meeting_name = Column(String(200), nullable=False, comment='会议名称')

    # 时间地点
    meeting_date = Column(Date, nullable=False, comment='会议日期')
    start_time = Column(Time, comment='开始时间')
    end_time = Column(Time, comment='结束时间')
    location = Column(String(100), comment='会议地点')

    # 人员
    organizer_id = Column(Integer, ForeignKey('users.id'), comment='组织者ID')
    organizer_name = Column(String(50), comment='组织者')
    attendees = Column(JSON, comment='参会人员')

    # 内容
    agenda = Column(Text, comment='会议议程')
    minutes = Column(Text, comment='会议纪要')
    decisions = Column(Text, comment='会议决议')
    action_items = Column(JSON, comment='待办事项')

    # 附件
    attachments = Column(JSON, comment='会议附件')

    # 状态
    status = Column(String(20), default='SCHEDULED', comment='状态:SCHEDULED/ONGOING/COMPLETED/CANCELLED')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    __table_args__ = (
        Index('idx_pmo_meeting_project', 'project_id'),
        Index('idx_pmo_meeting_date', 'meeting_date'),
        Index('idx_pmo_meeting_type', 'meeting_type'),
        {'comment': '项目会议表'}
    )


# ==================== 资源分配 ====================

class PmoResourceAllocation(Base, TimestampMixin):
    """项目资源分配"""
    __tablename__ = 'pmo_resource_allocation'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    task_id = Column(Integer, comment='任务ID')

    # 资源信息
    resource_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='资源ID(人员ID)')
    resource_name = Column(String(50), comment='资源名称')
    resource_dept = Column(String(50), comment='所属部门')
    resource_role = Column(String(50), comment='项目角色')

    # 分配信息
    allocation_percent = Column(Integer, default=100, comment='分配比例(%)')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    planned_hours = Column(Integer, comment='计划工时')
    actual_hours = Column(Integer, default=0, comment='实际工时')

    # 状态
    status = Column(String(20), default='PLANNED', comment='状态')

    __table_args__ = (
        Index('idx_pmo_alloc_project', 'project_id'),
        Index('idx_pmo_alloc_resource', 'resource_id'),
        Index('idx_pmo_alloc_dates', 'start_date', 'end_date'),
        {'comment': '项目资源分配表'}
    )


# ==================== 项目结项 ====================

class PmoProjectClosure(Base, TimestampMixin):
    """项目结项"""
    __tablename__ = 'pmo_project_closure'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, unique=True, comment='项目ID')

    # 验收信息
    acceptance_date = Column(Date, comment='验收日期')
    acceptance_result = Column(String(20), comment='验收结果:PASSED/CONDITIONAL/FAILED')
    acceptance_notes = Column(Text, comment='验收说明')

    # 项目总结
    project_summary = Column(Text, comment='项目总结')
    achievement = Column(Text, comment='项目成果')
    lessons_learned = Column(Text, comment='经验教训')
    improvement_suggestions = Column(Text, comment='改进建议')

    # 成本核算
    final_budget = Column(Numeric(14, 2), comment='最终预算')
    final_cost = Column(Numeric(14, 2), comment='最终成本')
    cost_variance = Column(Numeric(14, 2), comment='成本偏差')

    # 工时核算
    final_planned_hours = Column(Integer, comment='最终计划工时')
    final_actual_hours = Column(Integer, comment='最终实际工时')
    hours_variance = Column(Integer, comment='工时偏差')

    # 进度核算
    plan_duration = Column(Integer, comment='计划周期(天)')
    actual_duration = Column(Integer, comment='实际周期(天)')
    schedule_variance = Column(Integer, comment='进度偏差(天)')

    # 质量评估
    quality_score = Column(Integer, comment='质量评分')
    customer_satisfaction = Column(Integer, comment='客户满意度')

    # 文档归档
    archive_status = Column(String(20), comment='归档状态:PENDING/ARCHIVING/COMPLETED')
    archive_path = Column(String(500), comment='归档路径')

    # 结项评审
    closure_date = Column(Date, comment='结项日期')
    reviewed_by = Column(Integer, ForeignKey('users.id'), comment='评审人')
    review_date = Column(Date, comment='评审日期')
    review_result = Column(String(20), comment='评审结果:APPROVED/REJECTED')

    __table_args__ = (
        {'comment': '项目结项表'}
    )
