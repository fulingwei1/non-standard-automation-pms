# -*- coding: utf-8 -*-
"""
组织架构模型 (员工、部门)
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    """部门表"""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dept_code = Column(String(20), unique=True, nullable=False, comment="部门编码")
    dept_name = Column(String(50), nullable=False, comment="部门名称")
    parent_id = Column(Integer, ForeignKey("departments.id"), comment="父部门ID")
    manager_id = Column(Integer, ForeignKey("employees.id"), comment="部门负责人ID")
    level = Column(Integer, default=1, comment="层级")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    parent = relationship("Department", remote_side=[id], backref="children")
    manager = relationship("Employee", foreign_keys=[manager_id])
    # projects relationship is defined in Project model with backref or manual

    def __repr__(self):
        return f"<Department {self.dept_name}>"


class Employee(Base, TimestampMixin):
    """员工表"""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_code = Column(String(10), unique=True, nullable=False, comment="工号")
    name = Column(String(50), nullable=False, comment="姓名")
    department = Column(String(50), comment="部门")  # Legacy string field
    role = Column(String(50), comment="角色")
    phone = Column(String(20), comment="电话")
    wechat_userid = Column(String(50), comment="企业微信UserID")
    is_active = Column(Boolean, default=True, comment="是否在职")

    # 关系
    # user = relationship('User', back_populates='employee')

    def __repr__(self):
        return f"<Employee {self.name}>"
