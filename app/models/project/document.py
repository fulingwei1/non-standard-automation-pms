# -*- coding: utf-8 -*-
"""
项目文档和模板模型 - ProjectDocument, ProjectTemplate, ProjectTemplateVersion
"""

from sqlalchemy import (
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

from ..base import Base, TimestampMixin
from ..rd_project import RdProject


class ProjectDocument(Base, TimestampMixin):
    """项目文档表"""

    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")
    rd_project_id = Column(Integer, ForeignKey("rd_project.id"), comment="研发项目ID")
    doc_type = Column(String(50), nullable=False, comment="文档类型")
    doc_category = Column(String(50), comment="文档分类")
    doc_name = Column(String(200), nullable=False, comment="文档名称")
    doc_no = Column(String(100), comment="文档编号")
    version = Column(String(20), default="1.0", comment="版本号")

    # 文件信息
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_name = Column(String(200), nullable=False, comment="文件名")
    file_size = Column(Integer, comment="文件大小")
    file_type = Column(String(50), comment="文件类型")

    # 状态
    status = Column(String(20), default="DRAFT", comment="状态")

    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")

    description = Column(Text, comment="描述")
    uploaded_by = Column(Integer, ForeignKey("users.id"), comment="上传人")

    # 关系
    project = relationship("Project", back_populates="documents")
    rd_project = relationship(
        RdProject,
        foreign_keys=[rd_project_id],
        back_populates="documents",
    )
    machine = relationship("Machine")

    __table_args__ = (
        Index("idx_project_documents_project", "project_id"),
        Index("idx_project_documents_rd_project", "rd_project_id"),
        Index("idx_project_documents_type", "doc_type"),
    )


class ProjectTemplate(Base, TimestampMixin):
    """项目模板表"""

    __tablename__ = "project_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")

    # 模板配置（JSON格式存储项目默认配置）
    project_type = Column(String(20), comment="项目类型")
    product_category = Column(String(50), comment="产品类别")
    industry = Column(String(50), comment="行业")

    # 默认配置
    default_stage = Column(String(20), default="S1", comment="默认阶段")
    default_status = Column(String(20), default="ST01", comment="默认状态")
    default_health = Column(String(10), default="H1", comment="默认健康度")

    # 模板内容（JSON格式，存储项目字段的默认值）
    template_config = Column(Text, comment="模板配置JSON")

    # 是否启用
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")

    # 版本管理
    current_version_id = Column(Integer, ForeignKey("project_template_versions.id"), comment="当前版本ID")

    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    versions = relationship("ProjectTemplateVersion", back_populates="template", foreign_keys="ProjectTemplateVersion.template_id", cascade="all, delete-orphan")
    current_version = relationship("ProjectTemplateVersion", foreign_keys=[current_version_id], post_update=True)

    __table_args__ = (
        Index("idx_project_template_code", "template_code"),
        Index("idx_project_template_active", "is_active"),
        Index("idx_project_template_current_version", "current_version_id"),
    )

    def __repr__(self):
        return f"<ProjectTemplate {self.template_code}>"


class ProjectTemplateVersion(Base, TimestampMixin):
    """项目模板版本表"""

    __tablename__ = "project_template_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("project_templates.id"), nullable=False, comment="模板ID")
    version_no = Column(String(20), nullable=False, comment="版本号")
    status = Column(String(20), default="DRAFT", comment="状态：DRAFT/ACTIVE/ARCHIVED")
    template_config = Column(Text, comment="模板配置JSON")
    release_notes = Column(Text, comment="版本说明")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    published_by = Column(Integer, ForeignKey("users.id"), comment="发布人ID")
    published_at = Column(DateTime, comment="发布时间")

    # 关系
    template = relationship("ProjectTemplate", back_populates="versions", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by], backref="project_template_versions_created")
    publisher = relationship("User", foreign_keys=[published_by], backref="project_template_versions_published")

    __table_args__ = (
        Index("idx_project_template_version_template", "template_id"),
        Index("idx_project_template_version_status", "status"),
        Index("idx_project_template_version_unique", "template_id", "version_no", unique=True),
    )

    def __repr__(self):
        return f"<ProjectTemplateVersion {self.template_id}-{self.version_no}>"
