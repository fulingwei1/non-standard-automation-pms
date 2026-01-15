# -*- coding: utf-8 -*-
"""
组织架构模型 v2
支持公司/事业部/部门/团队的树形结构，以及岗位、职级体系
"""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class OrganizationUnitType(str, Enum):
    """组织单元类型"""
    COMPANY = "COMPANY"              # 公司
    BUSINESS_UNIT = "BUSINESS_UNIT"  # 事业部
    DEPARTMENT = "DEPARTMENT"        # 部门
    TEAM = "TEAM"                    # 团队


class PositionCategory(str, Enum):
    """岗位类别"""
    MANAGEMENT = "MANAGEMENT"    # 管理类
    TECHNICAL = "TECHNICAL"      # 技术类
    SUPPORT = "SUPPORT"          # 支持类
    SALES = "SALES"              # 销售类
    PRODUCTION = "PRODUCTION"    # 生产类


class JobLevelCategory(str, Enum):
    """职级序列"""
    P = "P"  # 专业序列
    M = "M"  # 管理序列
    T = "T"  # 技术序列


class AssignmentType(str, Enum):
    """员工分配类型"""
    PERMANENT = "PERMANENT"    # 正式分配
    TEMPORARY = "TEMPORARY"    # 临时借调
    PROJECT = "PROJECT"        # 项目分配


class OrganizationUnit(Base, TimestampMixin):
    """
    组织单元表
    支持公司/事业部/部门/团队的树形结构
    """
    __tablename__ = "organization_units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_code = Column(String(50), unique=True, nullable=False, comment="组织编码")
    unit_name = Column(String(100), nullable=False, comment="组织名称")
    unit_type = Column(
        String(20), nullable=False,
        comment="类型: COMPANY/BUSINESS_UNIT/DEPARTMENT/TEAM"
    )
    parent_id = Column(Integer, ForeignKey("organization_units.id"), comment="上级组织ID")
    manager_id = Column(Integer, ForeignKey("employees.id"), comment="负责人ID")
    level = Column(Integer, default=1, comment="层级深度")
    path = Column(String(500), comment="路径(如: /1/3/5/)")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    parent = relationship("OrganizationUnit", remote_side=[id], backref="children")
    manager = relationship("Employee", foreign_keys=[manager_id])
    positions = relationship("Position", back_populates="org_unit")
    employee_assignments = relationship("EmployeeOrgAssignment", back_populates="org_unit")

    __table_args__ = (
        Index("idx_org_unit_type", "unit_type"),
        Index("idx_org_parent_id", "parent_id"),
        Index("idx_org_path", "path"),
        Index("idx_org_active", "is_active"),
    )

    def get_full_path_name(self) -> str:
        """获取完整路径名称"""
        names = [self.unit_name]
        parent = self.parent
        while parent:
            names.insert(0, parent.unit_name)
            parent = parent.parent
        return " / ".join(names)

    def get_all_children_ids(self) -> List[int]:
        """获取所有下级组织ID（包括自己）"""
        ids = [self.id]
        for child in self.children:
            ids.extend(child.get_all_children_ids())
        return ids

    def __repr__(self):
        return f"<OrganizationUnit(id={self.id}, code='{self.unit_code}', name='{self.unit_name}')>"


class Position(Base, TimestampMixin):
    """
    岗位表
    公司自定义的岗位体系
    """
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_code = Column(String(50), unique=True, nullable=False, comment="岗位编码")
    position_name = Column(String(100), nullable=False, comment="岗位名称")
    position_category = Column(
        String(20), nullable=False,
        comment="类别: MANAGEMENT/TECHNICAL/SUPPORT/SALES/PRODUCTION"
    )
    org_unit_id = Column(
        Integer, ForeignKey("organization_units.id"),
        comment="所属组织单元ID"
    )
    description = Column(Text, comment="岗位描述")
    responsibilities = Column(JSON, comment="岗位职责")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    org_unit = relationship("OrganizationUnit", back_populates="positions")
    position_roles = relationship("PositionRole", back_populates="position")
    employee_assignments = relationship("EmployeeOrgAssignment", back_populates="position")

    __table_args__ = (
        Index("idx_position_category", "position_category"),
        Index("idx_position_org", "org_unit_id"),
        Index("idx_position_active", "is_active"),
    )

    def get_default_roles(self) -> List["Role"]:
        """获取该岗位的默认角色"""
        return [pr.role for pr in self.position_roles if pr.is_active]

    def __repr__(self):
        return f"<Position(id={self.id}, code='{self.position_code}', name='{self.position_name}')>"


class JobLevel(Base, TimestampMixin):
    """
    职级表
    支持P序列(专业)、M序列(管理)、T序列(技术)
    """
    __tablename__ = "job_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level_code = Column(String(20), unique=True, nullable=False, comment="职级编码(如P1-P10)")
    level_name = Column(String(50), nullable=False, comment="职级名称")
    level_category = Column(String(10), nullable=False, comment="序列: P/M/T")
    level_rank = Column(Integer, nullable=False, comment="职级数值(用于比较)")
    description = Column(Text, comment="职级描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    employee_assignments = relationship("EmployeeOrgAssignment", back_populates="job_level")

    __table_args__ = (
        Index("idx_level_rank", "level_rank"),
        Index("idx_level_category", "level_category"),
    )

    def is_higher_than(self, other: "JobLevel") -> bool:
        """判断是否高于另一职级"""
        return self.level_rank > other.level_rank

    def __repr__(self):
        return f"<JobLevel(id={self.id}, code='{self.level_code}', rank={self.level_rank})>"


class EmployeeOrgAssignment(Base, TimestampMixin):
    """
    员工组织分配表
    支持一人多岗、矩阵式管理
    """
    __tablename__ = "employee_org_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False, comment="员工ID"
    )
    org_unit_id = Column(
        Integer, ForeignKey("organization_units.id", ondelete="CASCADE"),
        nullable=False, comment="组织单元ID"
    )
    position_id = Column(
        Integer, ForeignKey("positions.id", ondelete="SET NULL"),
        comment="岗位ID"
    )
    job_level_id = Column(
        Integer, ForeignKey("job_levels.id", ondelete="SET NULL"),
        comment="职级ID"
    )
    is_primary = Column(Boolean, default=True, comment="是否主要归属")
    assignment_type = Column(
        String(20), default=AssignmentType.PERMANENT.value,
        comment="分配类型: PERMANENT/TEMPORARY/PROJECT"
    )
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    is_active = Column(Boolean, default=True, comment="是否有效")

    # 关系
    employee = relationship("Employee", backref="org_assignments")
    org_unit = relationship("OrganizationUnit", back_populates="employee_assignments")
    position = relationship("Position", back_populates="employee_assignments")
    job_level = relationship("JobLevel", back_populates="employee_assignments")

    __table_args__ = (
        Index("idx_eoa_employee", "employee_id"),
        Index("idx_eoa_org_unit", "org_unit_id"),
        Index("idx_eoa_position", "position_id"),
        Index("idx_eoa_primary", "is_primary"),
        Index("idx_eoa_active", "is_active"),
        UniqueConstraint("employee_id", "org_unit_id", "is_primary", name="uk_eoa_emp_org_primary"),
    )

    def is_valid(self) -> bool:
        """检查分配是否有效"""
        if not self.is_active:
            return False
        today = date.today()
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True

    def __repr__(self):
        return f"<EmployeeOrgAssignment(employee_id={self.employee_id}, org_unit_id={self.org_unit_id}, primary={self.is_primary})>"


class PositionRole(Base):
    """
    岗位默认角色表
    定义岗位与系统角色的映射关系
    """
    __tablename__ = "position_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(
        Integer, ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False, comment="岗位ID"
    )
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False, comment="角色ID"
    )
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关系
    position = relationship("Position", back_populates="position_roles")
    role = relationship("Role", backref="position_roles")

    __table_args__ = (
        UniqueConstraint("position_id", "role_id", name="uk_position_role"),
        Index("idx_pr_position", "position_id"),
        Index("idx_pr_role", "role_id"),
    )

    def __repr__(self):
        return f"<PositionRole(position_id={self.position_id}, role_id={self.role_id})>"
