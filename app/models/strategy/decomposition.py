# -*- coding: utf-8 -*-
"""
目标分解模型 - DepartmentObjective, PersonalKPI
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class DepartmentObjective(Base, TimestampMixin):
    """部门目标 - 承接战略"""

    __tablename__ = "department_objectives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="关联战略")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, comment="部门ID")

    # 时间
    year = Column(Integer, nullable=False, comment="年度")
    quarter = Column(Integer, comment="季度（可选，如按季度分解）")

    # 目标内容
    objectives = Column(Text, comment="部门级目标列表（JSON）")
    key_results = Column(Text, comment="关键成果（JSON）")

    # KPI 配置
    kpis_config = Column(Text, comment="部门级 KPI 配置（JSON）")

    # 状态
    status = Column(String(20), default="DRAFT", comment="状态：DRAFT/CONFIRMED/IN_PROGRESS/COMPLETED")

    # 责任人
    owner_user_id = Column(Integer, ForeignKey("users.id"), comment="部门负责人")

    # 审批
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(String(50), comment="审批时间")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    strategy = relationship("Strategy", back_populates="department_objectives")
    department = relationship("Department")
    owner = relationship("User", foreign_keys=[owner_user_id])
    approver = relationship("User", foreign_keys=[approved_by])
    personal_kpis = relationship("PersonalKPI", back_populates="department_objective", lazy="dynamic")

    __table_args__ = (
        Index("idx_dept_objectives_strategy", "strategy_id"),
        Index("idx_dept_objectives_dept", "department_id"),
        Index("idx_dept_objectives_year", "year"),
        Index("idx_dept_objectives_status", "status"),
        Index("idx_dept_objectives_unique", "strategy_id", "department_id", "year", "quarter", unique=True),
    )

    def __repr__(self):
        return f"<DepartmentObjective dept={self.department_id} year={self.year}>"


class PersonalKPI(Base, TimestampMixin):
    """个人 KPI - 最终落地"""

    __tablename__ = "personal_kpis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="员工ID")

    # 时间
    year = Column(Integer, nullable=False, comment="年度")
    quarter = Column(Integer, comment="季度")

    # 来源追溯
    source_type = Column(String(20), nullable=False, comment="来源类型：CSF_KPI/DEPT_OBJECTIVE/ANNUAL_WORK")
    source_id = Column(Integer, comment="来源 ID")

    # 关联部门目标
    department_objective_id = Column(Integer, ForeignKey("department_objectives.id"), comment="部门目标ID")

    # KPI 内容
    kpi_name = Column(String(200), nullable=False, comment="KPI 名称")
    kpi_description = Column(Text, comment="KPI 描述")
    unit = Column(String(20), comment="单位")

    # 目标与完成
    target_value = Column(Numeric(14, 2), comment="目标值")
    actual_value = Column(Numeric(14, 2), comment="实际值")
    completion_rate = Column(Numeric(5, 2), comment="完成率（%）")

    # 权重
    weight = Column(Numeric(5, 2), default=0, comment="权重（%）")

    # 评分
    self_rating = Column(Integer, comment="自评分（1-100）")
    self_comment = Column(Text, comment="自评说明")
    manager_rating = Column(Integer, comment="主管评分（1-100）")
    manager_comment = Column(Text, comment="主管评语")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态：PENDING/SELF_RATED/MANAGER_RATED/CONFIRMED")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    employee = relationship("User", foreign_keys=[employee_id])
    department_objective = relationship("DepartmentObjective", back_populates="personal_kpis")

    __table_args__ = (
        Index("idx_personal_kpis_employee", "employee_id"),
        Index("idx_personal_kpis_year", "year"),
        Index("idx_personal_kpis_quarter", "quarter"),
        Index("idx_personal_kpis_source", "source_type", "source_id"),
        Index("idx_personal_kpis_dept_obj", "department_objective_id"),
        Index("idx_personal_kpis_status", "status"),
        Index("idx_personal_kpis_active", "is_active"),
    )

    def __repr__(self):
        return f"<PersonalKPI employee={self.employee_id} year={self.year}>"
