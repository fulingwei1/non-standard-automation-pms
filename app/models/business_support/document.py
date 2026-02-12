# -*- coding: utf-8 -*-
"""
商务支持模块 - 文件归档模型
"""

from sqlalchemy import Column, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class DocumentArchive(Base, TimestampMixin):
    """文件归档表"""

    __tablename__ = "document_archives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    archive_no = Column(String(50), unique=True, nullable=False, comment="归档编号")
    document_type = Column(String(50), comment="文件类型：contract/acceptance/invoice/other")
    related_type = Column(String(50), comment="关联类型：contract/project/acceptance")
    related_id = Column(Integer, comment="关联ID")
    document_name = Column(String(200), comment="文件名称")
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    archive_location = Column(String(200), comment="归档位置")
    archive_date = Column(Date, comment="归档日期")
    archiver_id = Column(Integer, ForeignKey("users.id"), comment="归档人ID")
    status = Column(String(20), default="archived", comment="状态：archived/borrowed/returned")
    remark = Column(Text, comment="备注")

    # 关系
    archiver = relationship("User", foreign_keys=[archiver_id])

    __table_args__ = (
        Index("idx_archive_no", "archive_no"),
        Index("idx_archive_document_type", "document_type"),
        Index("idx_related", "related_type", "related_id"),
    )

    def __repr__(self):
        return f"<DocumentArchive {self.archive_no}>"
