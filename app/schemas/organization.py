# -*- coding: utf-8 -*-
"""
组织架构 Schema
"""

from typing import Optional
from pydantic import BaseModel, Field


from .common import TimestampSchema


class DepartmentCreate(BaseModel):
    """创建部门"""

    dept_code: str = Field(max_length=20, description="部门编码")
    dept_name: str = Field(max_length=50, description="部门名称")
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    level: int = 1
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    """更新部门"""

    dept_name: Optional[str] = None
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DepartmentResponse(TimestampSchema):
    """部门响应"""

    id: int
    dept_code: str
    dept_name: str
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    level: int
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    """创建员工"""

    employee_code: str = Field(max_length=10, description="工号")
    name: str = Field(max_length=50, description="姓名")
    department: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    wechat_userid: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """更新员工"""

    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    wechat_userid: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(TimestampSchema):
    """员工响应"""

    id: int
    employee_code: str
    name: str
    department: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    wechat_userid: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
