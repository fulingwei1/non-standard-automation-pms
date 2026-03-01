# -*- coding: utf-8 -*-
"""
项目模板配置模型 - 支持可视化编辑和动态裁剪

包含：
- ProjectTemplateConfig: 模板配置主表
- StageConfig: 阶段配置（可启用/禁用/调整顺序）
- NodeConfig: 节点配置（可启用/禁用/调整顺序）
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProjectTemplateConfig(Base, TimestampMixin):
    """项目模板配置主表"""

    __tablename__ = "project_template_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_code = Column(String(50), unique=True, nullable=False, comment="配置编码")
    config_name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(Text, comment="配置描述")
    
    # 基于哪个预置模板
    base_template_code = Column(String(50), nullable=False, comment="基础模板编码")
    
    # 配置内容（JSON 格式，包含阶段和节点的启用状态、顺序等）
    config_json = Column(Text, comment="配置内容（JSON）")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否默认配置")
    
    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人 ID")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    stages = relationship(
        "StageConfig",
        back_populates="config",
        cascade="all, delete-orphan",
        order_by="StageConfig.sequence",
    )
    
    __table_args__ = (
        UniqueConstraint("config_code", name="uq_config_code"),
        {"comment": "项目模板配置表"}
    )


class StageConfig(Base, TimestampMixin):
    """阶段配置"""

    __tablename__ = "stage_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(
        Integer,
        ForeignKey("project_template_configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属配置 ID",
    )
    
    stage_code = Column(String(20), nullable=False, comment="阶段编码（S1/S2/...）")
    stage_name = Column(String(100), comment="阶段名称（可自定义）")
    sequence = Column(Integer, default=0, comment="排序序号")
    
    # 启用状态
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    is_required = Column(Boolean, default=False, comment="是否必需（必需阶段不可禁用）")
    
    # 自定义配置
    custom_description = Column(Text, comment="自定义描述")
    custom_estimated_days = Column(Integer, comment="自定义预计工期")
    
    # 关系
    config = relationship("ProjectTemplateConfig", back_populates="stages")
    nodes = relationship(
        "NodeConfig",
        back_populates="stage",
        cascade="all, delete-orphan",
        order_by="NodeConfig.sequence",
    )
    
    __table_args__ = (
        UniqueConstraint("config_id", "stage_code", name="uq_config_stage"),
        {"comment": "阶段配置表"}
    )


class NodeConfig(Base, TimestampMixin):
    """节点配置"""

    __tablename__ = "node_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_config_id = Column(
        Integer,
        ForeignKey("stage_configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属阶段配置 ID",
    )
    
    node_code = Column(String(20), nullable=False, comment="节点编码（S1N01/...）")
    node_name = Column(String(100), comment="节点名称（可自定义）")
    sequence = Column(Integer, default=0, comment="排序序号")
    
    # 启用状态
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    is_required = Column(Boolean, default=False, comment="是否必需（必需节点不可禁用）")
    
    # 自定义配置
    custom_owner_role_code = Column(String(50), comment="自定义负责人角色")
    custom_estimated_days = Column(Integer, comment="自定义预计工期")
    
    # 关系
    stage = relationship("StageConfig", back_populates="nodes")
    
    __table_args__ = (
        UniqueConstraint("stage_config_id", "node_code", name="uq_stage_node"),
        {"comment": "节点配置表"}
    )
