# -*- coding: utf-8 -*-
"""
用户与权限模型
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
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

    # 汇报关系：直接上级
    reporting_to = Column(Integer, ForeignKey("users.id"), comment="直接上级用户ID")

    # 方案生成积分系统
    solution_credits = Column(Integer, default=100, nullable=False, comment="方案生成积分余额")
    credits_updated_at = Column(DateTime, comment="积分最后变动时间")

    # 关系
    roles = relationship("UserRole", back_populates="user", lazy="dynamic")
    created_projects = relationship(
        "Project", back_populates="creator", foreign_keys="Project.created_by"
    )
    managed_projects = relationship(
        "Project", back_populates="manager", foreign_keys="Project.pm_id"
    )
    # 上下级关系
    manager = relationship("User", remote_side=[id], foreign_keys=[reporting_to], backref="subordinates")
    # 项目成员关系（补充缺失的反向关系）
    project_memberships = relationship("ProjectMember", back_populates="user", foreign_keys="ProjectMember.user_id")

    # ========================================================================
    # 便捷属性方法
    # ========================================================================

    @property
    def display_name(self) -> str:
        """获取用户显示名称（优先使用真实姓名）"""
        return self.real_name or self.username

    @property
    def full_info(self) -> dict:
        """获取用户完整信息"""
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'employee_no': self.employee_no,
            'department': self.department,
            'position': self.position,
            'email': self.email,
            'phone': self.phone,
            'avatar': self.avatar,
        }

    @property
    def is_manager(self) -> bool:
        """是否是管理者（有下属）"""
        return hasattr(self, 'subordinates') and list(self.subordinates)

    @property
    def role_codes(self) -> list:
        """获取用户所有角色编码"""
        return [r.role.role_code for r in self.roles.all()] if self.roles else []

    @property
    def has_sufficient_credits(self) -> bool:
        """是否有足够的积分（假设阈值为10）"""
        return self.solution_credits >= 10

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
    parent_id = Column(Integer, ForeignKey("roles.id"), nullable=True, comment="父角色ID（继承）")
    is_system = Column(Boolean, default=False, comment="是否系统预置")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    # 前端配置字段
    nav_groups = Column(JSON, comment="导航组配置（JSON数组）")
    ui_config = Column(JSON, comment="UI配置（JSON对象，包含导航、权限等前端配置）")

    # 关系
    users = relationship("UserRole", back_populates="role", lazy="dynamic")
    permissions = relationship("RolePermission", back_populates="role", lazy="dynamic")
    parent = relationship("Role", remote_side=[id], backref="children")

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
    module = Column(String(50), comment="所属模块编码")
    page_code = Column(String(50), nullable=True, comment="所属页面编码")
    # 以下字段在旧表结构中可能不存在，设为可选
    resource = Column(String(50), nullable=True, comment="资源类型")
    action = Column(String(20), comment="操作类型: VIEW/CREATE/EDIT/DELETE/APPROVE/EXPORT")
    depends_on = Column(Integer, ForeignKey("permissions.id"), nullable=True, comment="依赖的权限ID")
    description = Column(Text, nullable=True, comment="权限描述")
    is_active = Column(Boolean, default=True, nullable=True, comment="是否启用")

    # 关系
    roles = relationship("RolePermission", back_populates="permission", lazy="dynamic")
    parent_permission = relationship("Permission", remote_side=[id], backref="dependent_permissions")

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


class RoleTemplate(Base, TimestampMixin):
    """角色模板表"""

    __tablename__ = "role_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(30), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(50), nullable=False, comment="模板名称")
    role_type = Column(String(20), nullable=False, default="BUSINESS", comment="角色类型")
    scope_type = Column(String(20), default="GLOBAL", comment="范围类型")
    data_scope = Column(String(20), default="PROJECT", comment="数据权限范围")
    level = Column(Integer, default=2, comment="层级")
    description = Column(Text, comment="模板描述")
    permission_snapshot = Column(Text, comment="权限快照")
    is_active = Column(Boolean, default=True, comment="是否启用")

    def __repr__(self):
        return f"<RoleTemplate {self.template_code}>"


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


class SolutionCreditTransaction(Base):
    """方案生成积分交易记录表"""

    __tablename__ = "solution_credit_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 交易类型
    transaction_type = Column(String(30), nullable=False, comment="交易类型")
    # INIT: 初始化积分
    # GENERATE: 生成方案扣除
    # ADMIN_ADD: 管理员充值
    # ADMIN_DEDUCT: 管理员扣除
    # SYSTEM_REWARD: 系统奖励
    # REFUND: 退还（生成失败时）

    # 积分变动
    amount = Column(Integer, nullable=False, comment="变动数量（正为增加，负为减少）")
    balance_before = Column(Integer, nullable=False, comment="变动前余额")
    balance_after = Column(Integer, nullable=False, comment="变动后余额")

    # 关联信息
    related_type = Column(String(50), comment="关联对象类型")
    related_id = Column(Integer, comment="关联对象ID")

    # 操作信息
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    remark = Column(Text, comment="备注说明")

    # 元数据
    ip_address = Column(String(50), comment="操作IP")
    user_agent = Column(String(500), comment="用户代理")

    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", comment="创建时间")

    # 关系
    user = relationship("User", foreign_keys=[user_id], backref="credit_transactions")
    operator = relationship("User", foreign_keys=[operator_id])

    def __repr__(self):
        return f"<SolutionCreditTransaction {self.transaction_type} {self.amount}>"


class SolutionCreditConfig(Base):
    """方案生成积分配置表"""

    __tablename__ = "solution_credit_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False, comment="配置键")
    config_value = Column(String(200), nullable=False, comment="配置值")
    description = Column(Text, comment="配置说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", comment="创建时间")
    updated_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", comment="更新时间")

    def __repr__(self):
        return f"<SolutionCreditConfig {self.config_key}={self.config_value}>"
