# -*- coding: utf-8 -*-
"""
用户与权限模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
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
    # 前端配置字段
    nav_groups = Column(JSON, comment="导航组配置（JSON数组）")
    ui_config = Column(JSON, comment="UI配置（JSON对象，包含导航、权限等前端配置）")

    # 关系
    users = relationship("UserRole", back_populates="role", lazy="dynamic")
    permissions = relationship("RolePermission", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.role_code}>"


class Permission(Base, TimestampMixin):
    """权限表"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 兼容旧表结构：数据库使用 perm_code，模型使用 permission_code
    # 使用 name 参数映射到数据库字段名
    permission_code = Column(
        "perm_code", String(100), unique=True, nullable=False, comment="权限编码"
    )
    permission_name = Column("perm_name", String(200), nullable=False, comment="权限名称")
    module = Column(String(50), comment="所属模块")
    # 以下字段在旧表结构中可能不存在，设为可选
    resource = Column(String(50), nullable=True, comment="资源类型")
    action = Column(String(20), comment="操作类型")
    description = Column(Text, nullable=True, comment="权限描述")
    is_active = Column(Boolean, default=True, nullable=True, comment="是否启用")

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


class PermissionAudit(Base, TimestampMixin):
    """权限审计表"""

    __tablename__ = "permission_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="操作人ID"
    )
    action = Column(String(50), nullable=False, comment="操作类型")
    target_type = Column(String(20), nullable=False, comment="目标类型（user/role/permission）")
    target_id = Column(Integer, nullable=False, comment="目标ID")
    detail = Column(Text, comment="详细信息（JSON格式）")
    ip_address = Column(String(50), comment="操作IP地址")
    user_agent = Column(String(500), comment="用户代理")

    # 关系
    operator = relationship("User", foreign_keys=[operator_id])

    def __repr__(self):
        return f"<PermissionAudit {self.action} {self.target_type}:{self.target_id}>"
