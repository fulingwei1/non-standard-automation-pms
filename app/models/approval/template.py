# -*- coding: utf-8 -*-
"""
审批模板模型

定义可复用的审批流程模板，支持表单定义和版本管理
"""


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
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ApprovalTemplate(Base, TimestampMixin):
    """审批模板 - 定义可复用的审批流程模板"""

    __tablename__ = "approval_templates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(100), nullable=False, comment="模板名称")
    category = Column(String(20), comment="分类：HR/FINANCE/PROJECT/BUSINESS/ADMIN")
    description = Column(Text, comment="模板描述")
    icon = Column(String(50), comment="图标")

    # 关联业务实体类型
    entity_type = Column(String(50), comment="关联业务实体类型（如QUOTE/CONTRACT/ECN）")

    # 表单定义
    form_schema = Column(JSON, comment="""
        表单结构定义（JSON Schema），示例：
        {
            "fields": [
                {"name": "leave_type", "type": "select", "label": "请假类型", "required": true},
                {"name": "start_date", "type": "date", "label": "开始日期"},
                {"name": "leave_days", "type": "number", "label": "请假天数", "computed": true}
            ]
        }
    """)

    # 版本管理
    version = Column(Integer, default=1, comment="版本号")
    is_published = Column(Boolean, default=False, comment="是否已发布")
    published_at = Column(DateTime, comment="发布时间")
    published_by = Column(Integer, ForeignKey("users.id"), comment="发布人ID")

    # 权限控制
    visible_scope = Column(JSON, comment="""
        可见范围配置，示例：
        {
            "type": "ALL",  // ALL/DEPARTMENT/ROLE/USER
            "department_ids": [1, 2, 3],
            "role_codes": ["SALES", "PM"],
            "user_ids": [10, 20]
        }
    """)

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="最后更新人ID")

    # 关系
    flows = relationship("ApprovalFlowDefinition", back_populates="template", cascade="all, delete-orphan")
    routing_rules = relationship("ApprovalRoutingRule", back_populates="template", cascade="all, delete-orphan")
    instances = relationship("ApprovalInstance", back_populates="template")
    creator = relationship("User", foreign_keys=[created_by])
    publisher = relationship("User", foreign_keys=[published_by])

    __table_args__ = (
        Index("idx_approval_template_code", "template_code"),
        Index("idx_approval_template_category", "category"),
        Index("idx_approval_template_entity_type", "entity_type"),
        Index("idx_approval_template_active", "is_active"),
        Index("idx_approval_template_published", "is_published"),
    )

    def __repr__(self):
        return f"<ApprovalTemplate {self.template_code}: {self.template_name}>"


class ApprovalTemplateVersion(Base, TimestampMixin):
    """审批模板版本历史
    
    【状态】未启用 - 审批模板版本控制"""
    __tablename__ = "approval_template_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_id = Column(Integer, ForeignKey("approval_templates.id"), nullable=False, comment="模板ID")
    version = Column(Integer, nullable=False, comment="版本号")

    # 版本快照
    template_name = Column(String(100), comment="模板名称")
    form_schema = Column(JSON, comment="表单结构定义")
    flow_snapshot = Column(JSON, comment="流程定义快照")

    # 版本信息
    change_log = Column(Text, comment="变更说明")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    __table_args__ = (
        Index("idx_template_version_template", "template_id"),
        Index("idx_template_version_version", "template_id", "version", unique=True),
    )

    def __repr__(self):
        return f"<ApprovalTemplateVersion {self.template_id}-v{self.version}>"
