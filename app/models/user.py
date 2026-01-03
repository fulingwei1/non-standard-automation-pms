# -*- coding: utf-8 -*-
"""
用户与权限模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, comment="员工ID"
    )
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    auth_type = Column(String(20), default="password", comment="认证方式")
    email = Column(String(100), unique=True, comment="邮箱")
    phone = Column(String(20), comment="手机号")
    real_name = Column(String(50), comment="真实姓名")
    employee_no = Column(String(50), comment="工号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    avatar = Column(String(500), comment="头像URL")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    last_login_at = Column(DateTime, comment="最后登录时间")
    last_login_ip = Column(String(50), comment="最后登录IP")

    # 关系
    roles = relationship("UserRole", back_populates="user", lazy="dynamic")
    created_projects = relationship(
        "Project", back_populates="creator", foreign_keys="Project.created_by"
    )
    managed_projects = relationship(
        "Project", back_populates="manager", foreign_keys="Project.pm_id"
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Role(Base, TimestampMixin):
    """角色表"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_code = Column(String(50), unique=True, nullable=False, comment="角色编码")
    role_name = Column(String(100), nullable=False, comment="角色名称")
    description = Column(Text, comment="角色描述")
    data_scope = Column(String(20), default="OWN", comment="数据权限范围")
    is_system = Column(Boolean, default=False, comment="是否系统预置")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    users = relationship("UserRole", back_populates="role", lazy="dynamic")
    permissions = relationship("RolePermission", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.role_code}>"


class Permission(Base, TimestampMixin):
    """权限表"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_code = Column(
        String(100), unique=True, nullable=False, comment="权限编码"
    )
    permission_name = Column(String(200), nullable=False, comment="权限名称")
    module = Column(String(50), comment="所属模块")
    resource = Column(String(50), comment="资源类型")
    action = Column(String(20), comment="操作类型")
    description = Column(Text, comment="权限描述")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    roles = relationship("RolePermission", back_populates="permission", lazy="dynamic")

    def __repr__(self):
        return f"<Permission {self.permission_code}>"


class RolePermission(Base):
    """角色权限关联表"""

    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, comment="角色ID")
    permission_id = Column(
        Integer, ForeignKey("permissions.id"), nullable=False, comment="权限ID"
    )

    # 关系
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")


class UserRole(Base):
    """用户角色关联表"""

    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, comment="角色ID")

    # 关系
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
