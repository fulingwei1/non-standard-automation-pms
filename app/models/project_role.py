# -*- coding: utf-8 -*-
"""
项目角色类型与配置模型

支持后台灵活配置项目负责人角色类型
"""


from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ProjectRoleType(Base, TimestampMixin):
    """
    项目角色类型字典表

    定义系统中所有可用的项目角色类型，如：
    - PM: 项目经理
    - TECH_LEAD: 技术负责人
    - ME_LEAD: 机械负责人
    - EE_LEAD: 电气负责人
    - SW_LEAD: 软件负责人
    - PROC_LEAD: 采购负责人
    - CS_LEAD: 客服负责人
    - QA_LEAD: 质量负责人
    """

    __tablename__ = "project_role_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_code = Column(String(50), unique=True, nullable=False, comment="角色编码")
    role_name = Column(String(100), nullable=False, comment="角色名称")
    role_category = Column(
        String(50),
        default='GENERAL',
        comment="角色分类: MANAGEMENT(管理), TECHNICAL(技术), SUPPORT(支持)"
    )
    description = Column(Text, comment="角色职责描述")
    can_have_team = Column(Boolean, default=False, comment="是否可带团队")
    is_required = Column(Boolean, default=False, comment="是否默认必需（新项目自动启用）")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    role_configs = relationship("ProjectRoleConfig", back_populates="role_type")

    __table_args__ = (
        Index("idx_prt_category", "role_category"),
        Index("idx_prt_active", "is_active"),
        Index("idx_prt_sort", "sort_order"),
    )

    def __repr__(self):
        return f"<ProjectRoleType {self.role_code}: {self.role_name}>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "role_code": self.role_code,
            "role_name": self.role_name,
            "role_category": self.role_category,
            "description": self.description,
            "can_have_team": self.can_have_team,
            "is_required": self.is_required,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProjectRoleConfig(Base, TimestampMixin):
    """
    项目角色配置表

    配置每个项目启用哪些角色类型，以及该角色是否必须指定负责人
    """

    __tablename__ = "project_role_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    role_type_id = Column(
        Integer,
        ForeignKey("project_role_types.id"),
        nullable=False,
        comment="角色类型ID"
    )
    is_enabled = Column(Boolean, default=True, comment="是否启用该角色")
    is_required = Column(Boolean, default=False, comment="是否必填（必须指定负责人）")
    remark = Column(Text, comment="配置备注")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", backref="role_configs")
    role_type = relationship("ProjectRoleType", back_populates="role_configs")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_prc_project", "project_id"),
        Index("idx_prc_role", "role_type_id"),
        UniqueConstraint("project_id", "role_type_id", name="uq_project_role_config"),
    )

    def __repr__(self):
        return f"<ProjectRoleConfig Project={self.project_id} Role={self.role_type_id}>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "role_type_id": self.role_type_id,
            "role_type": self.role_type.to_dict() if self.role_type else None,
            "is_enabled": self.is_enabled,
            "is_required": self.is_required,
            "remark": self.remark,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# 角色分类常量
class RoleCategoryEnum:
    MANAGEMENT = "MANAGEMENT"  # 管理类：项目经理
    TECHNICAL = "TECHNICAL"    # 技术类：技术负责人、机械/电气/软件负责人
    SUPPORT = "SUPPORT"        # 支持类：采购、客服、质量负责人
    GENERAL = "GENERAL"        # 通用类

    @classmethod
    def choices(cls):
        return [
            (cls.MANAGEMENT, "管理类"),
            (cls.TECHNICAL, "技术类"),
            (cls.SUPPORT, "支持类"),
            (cls.GENERAL, "通用类"),
        ]


# 预置角色编码常量
class ProjectRoleCodeEnum:
    PM = "PM"                  # 项目经理
    TECH_LEAD = "TECH_LEAD"    # 技术负责人
    ME_LEAD = "ME_LEAD"        # 机械负责人
    EE_LEAD = "EE_LEAD"        # 电气负责人
    SW_LEAD = "SW_LEAD"        # 软件负责人
    PROC_LEAD = "PROC_LEAD"    # 采购负责人
    CS_LEAD = "CS_LEAD"        # 客服负责人
    QA_LEAD = "QA_LEAD"        # 质量负责人
    PMC_LEAD = "PMC_LEAD"      # PMC负责人
    INSTALL_LEAD = "INSTALL_LEAD"  # 安装负责人
