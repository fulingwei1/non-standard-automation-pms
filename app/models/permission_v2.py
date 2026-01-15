# -*- coding: utf-8 -*-
"""
权限模型 v2
支持数据权限规则、菜单权限、权限分组
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ScopeType(str, Enum):
    """数据权限范围类型"""
    ALL = "ALL"                      # 全部数据
    BUSINESS_UNIT = "BUSINESS_UNIT"  # 本事业部数据
    DEPARTMENT = "DEPARTMENT"        # 本部门数据
    TEAM = "TEAM"                    # 本团队数据
    PROJECT = "PROJECT"              # 参与项目数据
    OWN = "OWN"                      # 仅个人数据
    CUSTOM = "CUSTOM"                # 自定义规则


class MenuType(str, Enum):
    """菜单类型"""
    DIRECTORY = "DIRECTORY"  # 目录
    MENU = "MENU"            # 菜单
    BUTTON = "BUTTON"        # 按钮


class PermissionType(str, Enum):
    """权限类型"""
    API = "API"        # API权限
    MENU = "MENU"      # 菜单权限
    BUTTON = "BUTTON"  # 按钮权限
    DATA = "DATA"      # 数据权限


class DataScopeRule(Base, TimestampMixin):
    """
    数据权限规则表
    定义可复用的数据权限规则
    """
    __tablename__ = "data_scope_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_code = Column(String(50), unique=True, nullable=False, comment="规则编码")
    rule_name = Column(String(100), nullable=False, comment="规则名称")
    scope_type = Column(
        String(20), nullable=False,
        comment="范围类型: ALL/BUSINESS_UNIT/DEPARTMENT/TEAM/PROJECT/OWN/CUSTOM"
    )
    scope_config = Column(JSON, comment="范围配置(自定义规则时使用)")
    description = Column(Text, comment="规则描述")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    role_data_scopes = relationship("RoleDataScope", back_populates="scope_rule")

    __table_args__ = (
        Index("idx_dsr_scope_type", "scope_type"),
        Index("idx_dsr_active", "is_active"),
    )

    def get_scope_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        if self.scope_config:
            return self.scope_config if isinstance(self.scope_config, dict) else {}
        return {}

    def __repr__(self):
        return f"<DataScopeRule(id={self.id}, code='{self.rule_code}', type='{self.scope_type}')>"


class RoleDataScope(Base):
    """
    角色数据权限表
    定义角色对不同资源类型的数据权限
    """
    __tablename__ = "role_data_scopes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False, comment="角色ID"
    )
    resource_type = Column(
        String(50), nullable=False,
        comment="资源类型(project/customer/employee等)"
    )
    scope_rule_id = Column(
        Integer, ForeignKey("data_scope_rules.id", ondelete="RESTRICT"),
        nullable=False, comment="数据权限规则ID"
    )
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关系
    role = relationship("Role", backref="data_scopes")
    scope_rule = relationship("DataScopeRule", back_populates="role_data_scopes")

    __table_args__ = (
        UniqueConstraint("role_id", "resource_type", name="uk_role_resource"),
        Index("idx_rds_role", "role_id"),
        Index("idx_rds_resource", "resource_type"),
    )

    def __repr__(self):
        return f"<RoleDataScope(role_id={self.role_id}, resource='{self.resource_type}')>"


class PermissionGroup(Base, TimestampMixin):
    """
    权限分组表
    用于组织和分类权限
    """
    __tablename__ = "permission_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_code = Column(String(50), unique=True, nullable=False, comment="分组编码")
    group_name = Column(String(100), nullable=False, comment="分组名称")
    parent_id = Column(
        Integer, ForeignKey("permission_groups.id", ondelete="SET NULL"),
        comment="父分组ID"
    )
    description = Column(Text, comment="分组描述")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    parent = relationship("PermissionGroup", remote_side=[id], backref="children")

    __table_args__ = (
        Index("idx_pg_parent", "parent_id"),
    )

    def get_all_children(self) -> List["PermissionGroup"]:
        """获取所有子分组"""
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.get_all_children())
        return result

    def __repr__(self):
        return f"<PermissionGroup(id={self.id}, code='{self.group_code}', name='{self.group_name}')>"


class MenuPermission(Base, TimestampMixin):
    """
    菜单权限表
    管理前端菜单和按钮的权限配置
    """
    __tablename__ = "menu_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_code = Column(String(50), unique=True, nullable=False, comment="菜单编码")
    menu_name = Column(String(100), nullable=False, comment="菜单名称")
    menu_path = Column(String(200), comment="前端路由路径")
    menu_icon = Column(String(50), comment="菜单图标")
    parent_id = Column(
        Integer, ForeignKey("menu_permissions.id", ondelete="SET NULL"),
        comment="父菜单ID"
    )
    menu_type = Column(
        String(20), nullable=False,
        comment="类型: DIRECTORY/MENU/BUTTON"
    )
    permission_id = Column(
        Integer, ForeignKey("permissions.id", ondelete="SET NULL"),
        comment="关联的API权限ID"
    )
    sort_order = Column(Integer, default=0, comment="排序")
    is_visible = Column(Boolean, default=True, comment="是否可见")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    parent = relationship("MenuPermission", remote_side=[id], backref="children")
    permission = relationship("Permission", backref="menu_items")
    role_menus = relationship("RoleMenu", back_populates="menu")

    __table_args__ = (
        Index("idx_mp_parent", "parent_id"),
        Index("idx_mp_type", "menu_type"),
        Index("idx_mp_visible", "is_visible"),
        Index("idx_mp_active", "is_active"),
    )

    def to_dict(self, include_children: bool = True) -> Dict[str, Any]:
        """转换为字典（用于前端菜单构建）"""
        result = {
            "id": self.id,
            "code": self.menu_code,
            "name": self.menu_name,
            "path": self.menu_path,
            "icon": self.menu_icon,
            "type": self.menu_type,
            "visible": self.is_visible,
            "sort": self.sort_order,
        }
        if include_children and self.children:
            result["children"] = [
                child.to_dict(include_children=True)
                for child in sorted(self.children, key=lambda x: x.sort_order)
                if child.is_active and child.is_visible
            ]
        return result

    def get_all_children_ids(self) -> List[int]:
        """获取所有子菜单ID"""
        ids = [self.id]
        for child in self.children:
            ids.extend(child.get_all_children_ids())
        return ids

    def __repr__(self):
        return f"<MenuPermission(id={self.id}, code='{self.menu_code}', type='{self.menu_type}')>"


class RoleMenu(Base):
    """
    角色菜单关联表
    定义角色可访问的菜单
    """
    __tablename__ = "role_menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False, comment="角色ID"
    )
    menu_id = Column(
        Integer, ForeignKey("menu_permissions.id", ondelete="CASCADE"),
        nullable=False, comment="菜单ID"
    )
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关系
    role = relationship("Role", backref="menu_assignments")
    menu = relationship("MenuPermission", back_populates="role_menus")

    __table_args__ = (
        UniqueConstraint("role_id", "menu_id", name="uk_role_menu"),
        Index("idx_rm_role", "role_id"),
        Index("idx_rm_menu", "menu_id"),
    )

    def __repr__(self):
        return f"<RoleMenu(role_id={self.role_id}, menu_id={self.menu_id})>"


# ============================================================
# 用于扩展现有 Role 和 Permission 模型的字段
# 这些字段需要通过 ALTER TABLE 添加到现有表
# ============================================================

# 在 roles 表中需要添加的字段:
# - role_type: ENUM('SYSTEM', 'CUSTOM') DEFAULT 'CUSTOM'
# - role_category: VARCHAR(50)

# 在 permissions 表中需要添加的字段:
# - permission_type: ENUM('API', 'MENU', 'BUTTON', 'DATA') DEFAULT 'API'
# - group_id: INT REFERENCES permission_groups(id)


# ============================================================
# 常用资源类型常量
# ============================================================
class ResourceType:
    """资源类型常量"""
    PROJECT = "project"           # 项目
    CUSTOMER = "customer"         # 客户
    OPPORTUNITY = "opportunity"   # 商机
    QUOTE = "quote"               # 报价
    CONTRACT = "contract"         # 合同
    ORDER = "order"               # 订单
    EMPLOYEE = "employee"         # 员工
    MATERIAL = "material"         # 物料
    SUPPLIER = "supplier"         # 供应商
    PURCHASE = "purchase"         # 采购
    PRODUCTION = "production"     # 生产
    SERVICE = "service"           # 服务
    FINANCE = "finance"           # 财务
