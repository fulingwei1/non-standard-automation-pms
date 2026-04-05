# -*- coding: utf-8 -*-
"""
劳动力成本明细模型

记录项目各阶段的人工成本，包括方案设计、组装、调试、现场安装、培训等
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class WorkTypeEnum(str, Enum):
    """工作类型枚举"""

    DESIGN = "DESIGN"  # 方案设计
    ASSEMBLY = "ASSEMBLY"  # 组装
    DEBUG = "DEBUG"  # 调试
    INSTALLATION = "INSTALLATION"  # 现场安装
    TRAINING = "TRAINING"  # 培训
    REWORK = "REWORK"  # 返工
    SUPPORT = "SUPPORT"  # 技术支持
    OTHER = "OTHER"  # 其他


class LaborCostStatusEnum(str, Enum):
    """劳动力成本状态枚举"""

    ESTIMATED = "ESTIMATED"  # 预估
    IN_PROGRESS = "IN_PROGRESS"  # 进行中
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消


class ProjectLaborCostDetail(Base, TimestampMixin):
    """
    项目劳动力成本明细

    记录项目各阶段的人工成本，用于：
    1. 预估项目人工成本
    2. 跟踪实际人工投入
    3. 分析人工成本差异
    """

    __tablename__ = "project_labor_cost_details"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联信息
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="机台ID")

    # 工作类型
    work_type = Column(String(50), nullable=False, comment="工作类型")
    work_description = Column(String(500), comment="工作描述")

    # 人员信息
    engineer_id = Column(Integer, ForeignKey("users.id"), comment="工程师ID")
    engineer_name = Column(String(100), comment="工程师姓名")
    engineer_level = Column(String(50), comment="工程师级别（初级/中级/高级）")

    # 时间信息
    planned_start_date = Column(Date, comment="计划开始日期")
    planned_end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")

    # 工时信息
    estimated_hours = Column(Numeric(10, 2), default=0, comment="预估工时（小时）")
    actual_hours = Column(Numeric(10, 2), default=0, comment="实际工时（小时）")
    variance_hours = Column(Numeric(10, 2), default=0, comment="差异工时（小时）")

    # 成本信息
    hourly_rate = Column(Numeric(10, 2), default=0, comment="小时费率（元/小时）")
    estimated_cost = Column(Numeric(14, 2), default=0, comment="预估成本（元）")
    actual_cost = Column(Numeric(14, 2), default=0, comment="实际成本（元）")
    variance_cost = Column(Numeric(14, 2), default=0, comment="差异成本（元）")

    # 加班信息
    overtime_hours = Column(Numeric(10, 2), default=0, comment="加班工时（小时）")
    overtime_rate = Column(Numeric(10, 2), default=1.5, comment="加班费率倍数")
    overtime_cost = Column(Numeric(14, 2), default=0, comment="加班成本（元）")

    # 差旅信息（针对现场安装等）
    travel_days = Column(Integer, default=0, comment="出差天数")
    travel_allowance = Column(Numeric(10, 2), default=0, comment="出差补贴/天")
    travel_cost = Column(Numeric(14, 2), default=0, comment="差旅成本（元）")

    # 状态
    status = Column(String(50), default="ESTIMATED", comment="状态")

    # 工时单关联
    timesheet_ids = Column(JSON, comment="关联工时单ID列表")

    # 备注
    remark = Column(Text, comment="备注")

    # 审计
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    machine = relationship("Machine", foreign_keys=[machine_id])
    engineer = relationship("User", foreign_keys=[engineer_id])
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index("idx_labor_cost_project", "project_id"),
        Index("idx_labor_cost_machine", "machine_id"),
        Index("idx_labor_cost_work_type", "work_type"),
        Index("idx_labor_cost_engineer", "engineer_id"),
        Index("idx_labor_cost_status", "status"),
        {"comment": "项目劳动力成本明细表"},
    )

    def __repr__(self):
        return f"<ProjectLaborCostDetail {self.project_id}: {self.work_type}>"

    def calculate_costs(self):
        """计算成本（在保存前调用）"""
        # 预估成本 = 预估工时 * 小时费率
        self.estimated_cost = (self.estimated_hours or 0) * (self.hourly_rate or 0)

        # 实际成本 = 实际工时 * 小时费率 + 加班成本
        base_cost = (self.actual_hours or 0) * (self.hourly_rate or 0)
        self.overtime_cost = (
            (self.overtime_hours or 0) *
            (self.hourly_rate or 0) *
            ((self.overtime_rate or 1.5) - 1)  # 加班仅计算额外部分
        )
        self.actual_cost = base_cost + self.overtime_cost + (self.travel_cost or 0)

        # 差异
        self.variance_hours = (self.actual_hours or 0) - (self.estimated_hours or 0)
        self.variance_cost = (self.actual_cost or 0) - (self.estimated_cost or 0)


class ProjectLaborCostSummary(Base, TimestampMixin):
    """
    项目劳动力成本汇总

    按工作类型汇总项目的人工成本
    """

    __tablename__ = "project_labor_cost_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联信息
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")

    # 工作类型
    work_type = Column(String(50), nullable=False, comment="工作类型")

    # 工时汇总
    estimated_hours = Column(Numeric(10, 2), default=0, comment="预估工时总计")
    actual_hours = Column(Numeric(10, 2), default=0, comment="实际工时总计")
    variance_hours = Column(Numeric(10, 2), default=0, comment="差异工时")

    # 成本汇总
    estimated_cost = Column(Numeric(14, 2), default=0, comment="预估成本总计")
    actual_cost = Column(Numeric(14, 2), default=0, comment="实际成本总计")
    variance_cost = Column(Numeric(14, 2), default=0, comment="差异成本")
    variance_ratio = Column(Numeric(5, 2), default=0, comment="差异率(%)")

    # 人员统计
    engineer_count = Column(Integer, default=0, comment="投入人数")
    record_count = Column(Integer, default=0, comment="记录数量")

    # 最后计算时间
    calculated_at = Column(DateTime, default=datetime.now, comment="计算时间")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])

    __table_args__ = (
        Index("idx_labor_summary_project", "project_id"),
        Index("idx_labor_summary_work_type", "work_type"),
        Index("idx_labor_summary_unique", "project_id", "work_type", unique=True),
        {"comment": "项目劳动力成本汇总表"},
    )

    def __repr__(self):
        return f"<ProjectLaborCostSummary {self.project_id}: {self.work_type}>"
