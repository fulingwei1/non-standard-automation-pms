# -*- coding: utf-8 -*-
"""
项目阶段资源计划模型

支持按阶段规划人员需求、检测冲突、跟踪分配状态
"""

from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AssignmentStatusEnum(str, Enum):
    """资源分配状态"""
    PENDING = 'PENDING'       # 待分配
    ASSIGNED = 'ASSIGNED'     # 已分配
    CONFLICT = 'CONFLICT'     # 有冲突
    RELEASED = 'RELEASED'     # 已释放


class ConflictSeverityEnum(str, Enum):
    """冲突严重程度"""
    LOW = 'LOW'         # 低 - 总分配 100-120%
    MEDIUM = 'MEDIUM'   # 中 - 总分配 120-150%
    HIGH = 'HIGH'       # 高 - 总分配 >150%


class ProjectStageResourcePlan(Base, TimestampMixin):
    """项目阶段资源计划表"""
    __tablename__ = 'project_stage_resource_plan'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    stage_code = Column(String(10), nullable=False, comment='阶段编码 S1-S9')

    # 关联现有的人员需求表
    staffing_need_id = Column(Integer, ForeignKey('mes_project_staffing_need.id'), comment='关联人员需求ID')

    # 角色信息（冗余便于查询）
    role_code = Column(String(50), nullable=False, comment='角色编码')
    role_name = Column(String(100), comment='角色名称')
    headcount = Column(Integer, default=1, comment='需求人数')
    allocation_pct = Column(Numeric(5, 2), default=100, comment='分配比例%')

    # 实际分配
    assigned_employee_id = Column(Integer, ForeignKey('users.id'), comment='已分配员工ID')
    assignment_status = Column(
        String(20),
        default=AssignmentStatusEnum.PENDING.value,
        comment='分配状态: PENDING/ASSIGNED/CONFLICT/RELEASED'
    )

    # 时间范围
    planned_start = Column(Date, comment='计划开始日期')
    planned_end = Column(Date, comment='计划结束日期')

    # 备注
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    project = relationship('Project', backref='stage_resource_plans')
    staffing_need = relationship('MesProjectStaffingNeed')
    assigned_employee = relationship('User', foreign_keys=[assigned_employee_id])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_stage_plan_project', 'project_id'),
        Index('idx_stage_plan_stage', 'stage_code'),
        Index('idx_stage_plan_employee', 'assigned_employee_id'),
        Index('idx_stage_plan_status', 'assignment_status'),
        Index('idx_stage_plan_dates', 'planned_start', 'planned_end'),
        {'comment': '项目阶段资源计划表'}
    )

    @property
    def is_assigned(self) -> bool:
        """是否已分配"""
        return self.assignment_status == AssignmentStatusEnum.ASSIGNED.value

    @property
    def duration_days(self) -> Optional[int]:
        """计划持续天数"""
        if self.planned_start and self.planned_end:
            return (self.planned_end - self.planned_start).days
        return None


class ResourceConflict(Base, TimestampMixin):
    """资源冲突记录表"""
    __tablename__ = 'resource_conflicts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    employee_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='员工ID')

    # 冲突的两个资源计划
    plan_a_id = Column(Integer, ForeignKey('project_stage_resource_plan.id'), nullable=False, comment='计划A ID')
    plan_b_id = Column(Integer, ForeignKey('project_stage_resource_plan.id'), nullable=False, comment='计划B ID')

    # 冲突详情
    overlap_start = Column(Date, nullable=False, comment='重叠开始日期')
    overlap_end = Column(Date, nullable=False, comment='重叠结束日期')
    total_allocation = Column(Numeric(5, 2), comment='重叠期间总分配比例%')
    over_allocation = Column(Numeric(5, 2), comment='超额分配%')
    severity = Column(String(10), default=ConflictSeverityEnum.LOW.value, comment='严重程度')

    # 解决状态
    is_resolved = Column(Integer, default=0, comment='是否已解决 0-未解决 1-已解决')
    resolved_by = Column(Integer, ForeignKey('users.id'), comment='解决人ID')
    resolved_at = Column(Date, comment='解决日期')
    resolution_note = Column(Text, comment='解决说明')

    # 关系
    employee = relationship('User', foreign_keys=[employee_id])
    plan_a = relationship('ProjectStageResourcePlan', foreign_keys=[plan_a_id])
    plan_b = relationship('ProjectStageResourcePlan', foreign_keys=[plan_b_id])
    resolver = relationship('User', foreign_keys=[resolved_by])

    __table_args__ = (
        Index('idx_conflict_employee', 'employee_id'),
        Index('idx_conflict_resolved', 'is_resolved'),
        Index('idx_conflict_severity', 'severity'),
        {'comment': '资源冲突记录表'}
    )

    @property
    def overlap_days(self) -> int:
        """重叠天数"""
        return (self.overlap_end - self.overlap_start).days
