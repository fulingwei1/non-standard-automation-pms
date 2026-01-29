# -*- coding: utf-8 -*-
"""
统一权限模型
支持数据权限规则、菜单权限、权限分组、角色管理
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ScopeType(str, Enum):
    """数据权限范围类型"""

    ALL = "ALL"  # 全部数据
    BUSINESS_UNIT = "BUSINESS_UNIT"  # 本事业部数据
    DEPARTMENT = "DEPARTMENT"  # 本部门数据
    TEAM = "TEAM"  # 本团队数据
    PROJECT = "PROJECT"  # 参与项目数据
    OWN = "OWN"  # 仅个人数据
    CUSTOM = "CUSTOM"  # 自定义规则


class MenuType(str, Enum):
    """菜单类型"""

    DIRECTORY = "DIRECTORY"  # 目录
    MENU = "MENU"  # 菜单
    BUTTON = "BUTTON"  # 按钮


class PermissionType(str, Enum):
    """权限类型"""

    API = "API"  # API权限
    MENU = "MENU"  # 菜单权限
    BUTTON = "BUTTON"  # 按钮权限
    DATA = "DATA"  # 数据权限


class DataScopeRule(Base, TimestampMixin):
    """数据权限规则表

    多租户支持：
    - tenant_id = NULL: 系统级规则，所有租户共享
    - tenant_id = N: 租户自定义规则
    """

    __tablename__ = "data_scope_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 多租户支持
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID（NULL=系统级规则）"
    )
    rule_code = Column(String(50), nullable=False, comment="规则编码")
    rule_name = Column(String(100), nullable=False, comment="规则名称")
    scope_type = Column(String(20), nullable=False, comment="范围类型")
    scope_config = Column(JSON, comment="范围配置")
    description = Column(Text, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统预置")

    # 关系
    tenant = relationship("Tenant", backref="custom_data_scope_rules")
    role_data_scopes = relationship("RoleDataScope", back_populates="scope_rule")

    __table_args__ = (
        Index("idx_dsr_scope_type", "scope_type"),
        Index("idx_dsr_active", "is_active"),
        Index("idx_dsr_tenant", "tenant_id"),
        UniqueConstraint("tenant_id", "rule_code", name="uk_tenant_rule_code"),
    )


class RoleDataScope(Base):
    """角色数据权限关联表"""

    __tablename__ = "role_data_scopes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    resource_type = Column(String(50), nullable=False)
    scope_rule_id = Column(
        Integer, ForeignKey("data_scope_rules.id", ondelete="RESTRICT"), nullable=False
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    role = relationship("Role", backref="data_scopes")
    scope_rule = relationship("DataScopeRule", back_populates="role_data_scopes")

    __table_args__ = (
        UniqueConstraint("role_id", "resource_type", name="uk_role_resource"),
    )


class PermissionGroup(Base, TimestampMixin):
    """权限分组表"""

    __tablename__ = "permission_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_code = Column(String(50), unique=True, nullable=False)
    group_name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("permission_groups.id", ondelete="SET NULL"))
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    parent = relationship("PermissionGroup", remote_side=[id], backref="children")


class MenuPermission(Base, TimestampMixin):
    """菜单与按钮权限表

    多租户支持：
    - tenant_id = NULL: 系统级菜单，所有租户共享
    - tenant_id = N: 租户自定义菜单
    """

    __tablename__ = "menu_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 多租户支持
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID（NULL=系统级菜单）"
    )
    menu_code = Column(String(50), nullable=False, comment="菜单编码")
    menu_name = Column(String(100), nullable=False, comment="菜单名称")
    menu_path = Column(String(200), comment="前端路由路径")
    menu_icon = Column(String(50), comment="菜单图标")
    parent_id = Column(Integer, ForeignKey("menu_permissions.id", ondelete="SET NULL"), comment="父菜单ID")
    menu_type = Column(String(20), nullable=False, comment="类型: DIRECTORY/MENU/BUTTON")
    perm_code = Column(String(100), nullable=True, comment="关联的API权限编码（可选，纯目录可为NULL）")
    sort_order = Column(Integer, default=0, comment="排序")
    is_visible = Column(Boolean, default=True, comment="是否可见")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统预置菜单")

    # 关系
    tenant = relationship("Tenant", backref="custom_menus")
    parent = relationship("MenuPermission", remote_side=[id], backref="children")
    role_menus = relationship("RoleMenu", back_populates="menu")

    __table_args__ = (
        Index("idx_menu_tenant", "tenant_id"),
        Index("idx_menu_parent", "parent_id"),
        UniqueConstraint("tenant_id", "menu_code", name="uk_tenant_menu_code"),
    )


class RoleMenu(Base):
    """角色菜单关联表"""

    __tablename__ = "role_menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    menu_id = Column(
        Integer, ForeignKey("menu_permissions.id", ondelete="CASCADE"), nullable=False
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    role = relationship("Role", backref="menu_assignments")
    menu = relationship("MenuPermission", back_populates="role_menus")

    __table_args__ = (UniqueConstraint("role_id", "menu_id", name="uk_role_menu"),)


class ResourceType:
    """资源类型常量"""

    PROJECT = "project"  # 项目
    CUSTOMER = "customer"  # 客户
    OPPORTUNITY = "opportunity"  # 商机
    QUOTE = "quote"  # 报价
    CONTRACT = "contract"  # 合同
    ORDER = "order"  # 订单
    EMPLOYEE = "employee"  # 员工
    MATERIAL = "material"  # 物料
    SUPPLIER = "supplier"  # 供应商
    PURCHASE = "purchase"  # 采购
    PRODUCTION = "production"  # 生产
    SERVICE = "service"  # 服务
    FINANCE = "finance"  # 财务
