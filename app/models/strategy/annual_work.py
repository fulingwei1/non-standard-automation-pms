# -*- coding: utf-8 -*-
"""
年度重点工作模型 - AnnualKeyWork
"""

from sqlalchemy import (
    Boolean,
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

from ..base import Base, TimestampMixin


class AnnualKeyWork(Base, TimestampMixin):
    """年度重点工作 - VOC 法导出"""

    __tablename__ = "annual_key_works"

    id = Column(Integer, primary_key=True, autoincrement=True)
    csf_id = Column(Integer, ForeignKey("csfs.id"), nullable=False, comment="关联 CSF")

    # 基本信息
    code = Column(String(50), nullable=False, comment="工作编码，如 AKW-2026-001")
    name = Column(String(200), nullable=False, comment="工作名称")
    description = Column(Text, comment="工作描述")

    # VOC 来源
    voc_source = Column(String(20), comment="声音来源：SHAREHOLDER/CUSTOMER/EMPLOYEE/COMPLIANCE")
    pain_point = Column(Text, comment="识别的痛点/短板")
    solution = Column(Text, comment="解决方案")
    target = Column(Text, comment="目标描述")

    # 时间计划
    year = Column(Integer, nullable=False, comment="年度")
    start_date = Column(Date, comment="计划开始日期")
    end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")

    # 责任人
    owner_dept_id = Column(Integer, ForeignKey("departments.id"), comment="责任部门")
    owner_user_id = Column(Integer, ForeignKey("users.id"), comment="责任人")

    # 状态与进度
    status = Column(String(20), default="NOT_STARTED", comment="状态：NOT_STARTED/IN_PROGRESS/COMPLETED/DELAYED/CANCELLED")
    progress_percent = Column(Integer, default=0, comment="完成进度（%）")

    # 优先级
    priority = Column(String(20), default="MEDIUM", comment="优先级：HIGH/MEDIUM/LOW")

    # 资源需求
    budget = Column(Numeric(14, 2), comment="预算金额")
    actual_cost = Column(Numeric(14, 2), comment="实际成本")

    # 风险与备注
    risk_description = Column(Text, comment="风险描述")
    remark = Column(Text, comment="备注")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    csf = relationship("CSF", back_populates="annual_key_works")
    owner_dept = relationship("Department", foreign_keys=[owner_dept_id])
    owner = relationship("User", foreign_keys=[owner_user_id])
    project_links = relationship("AnnualKeyWorkProjectLink", back_populates="annual_work", lazy="dynamic")

    __table_args__ = (
        Index("idx_annual_key_works_csf", "csf_id"),
        Index("idx_annual_key_works_year", "year"),
        Index("idx_annual_key_works_code", "code"),
        Index("idx_annual_key_works_status", "status"),
        Index("idx_annual_key_works_owner_dept", "owner_dept_id"),
        Index("idx_annual_key_works_owner", "owner_user_id"),
        Index("idx_annual_key_works_active", "is_active"),
    )

    def __repr__(self):
        return f"<AnnualKeyWork {self.code}>"


class AnnualKeyWorkProjectLink(Base, TimestampMixin):
    """重点工作与项目关联"""

    __tablename__ = "annual_key_work_project_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    annual_work_id = Column(Integer, ForeignKey("annual_key_works.id"), nullable=False, comment="重点工作ID")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")

    # 关联类型
    link_type = Column(String(20), default="SUPPORT", comment="关联类型：MAIN/SUPPORT/RELATED")

    # 贡献度
    contribution_weight = Column(Numeric(5, 2), default=100, comment="贡献权重（%）")

    # 备注
    remark = Column(Text, comment="备注")

    # 关系
    annual_work = relationship("AnnualKeyWork", back_populates="project_links")
    project = relationship("Project")

    __table_args__ = (
        Index("idx_akw_project_links_work", "annual_work_id"),
        Index("idx_akw_project_links_project", "project_id"),
        Index("idx_akw_project_links_unique", "annual_work_id", "project_id", unique=True),
    )

    def __repr__(self):
        return f"<AnnualKeyWorkProjectLink work={self.annual_work_id} project={self.project_id}>"
