# -*- coding: utf-8 -*-
"""
商务支持模块 - 投标管理模型
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class BiddingProject(Base, TimestampMixin):
    """投标项目表"""

    __tablename__ = "bidding_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bidding_no = Column(String(50), unique=True, nullable=False, comment="投标编号")
    project_name = Column(String(500), nullable=False, comment="项目名称")
    customer_id = Column(Integer, ForeignKey("customers.id"), comment="客户ID")
    customer_name = Column(String(200), comment="客户名称")

    # 招标信息
    tender_no = Column(String(100), comment="招标编号")
    tender_type = Column(String(20), comment="招标类型：public/invited/competitive/single_source/online")
    tender_platform = Column(String(200), comment="招标平台")
    tender_url = Column(String(500), comment="招标链接")

    # 时间节点
    publish_date = Column(Date, comment="发布日期")
    deadline_date = Column(DateTime, comment="投标截止时间")
    bid_opening_date = Column(DateTime, comment="开标时间")

    # 标书信息
    bid_bond = Column(Numeric(15, 2), comment="投标保证金")
    bid_bond_status = Column(String(20), default="not_required", comment="保证金状态：not_required/pending/paid/returned")
    estimated_amount = Column(Numeric(15, 2), comment="预估金额")

    # 投标准备
    bid_document_status = Column(String(20), default="not_started", comment="标书状态：not_started/in_progress/completed/submitted")
    technical_doc_ready = Column(Boolean, default=False, comment="技术文件就绪")
    commercial_doc_ready = Column(Boolean, default=False, comment="商务文件就绪")
    qualification_doc_ready = Column(Boolean, default=False, comment="资质文件就绪")

    # 投标方式
    submission_method = Column(String(20), comment="投递方式：offline/online/both")
    submission_address = Column(String(500), comment="投递地址")

    # 负责人
    sales_person_id = Column(Integer, ForeignKey("users.id"), comment="业务员ID")
    sales_person_name = Column(String(50), comment="业务员")
    support_person_id = Column(Integer, ForeignKey("users.id"), comment="商务支持ID")
    support_person_name = Column(String(50), comment="商务支持")

    # 投标结果
    bid_result = Column(String(20), default="pending", comment="投标结果：pending/won/lost/cancelled/invalid")
    bid_price = Column(Numeric(15, 2), comment="投标价格")
    win_price = Column(Numeric(15, 2), comment="中标价格")
    result_date = Column(Date, comment="结果公布日期")
    result_remark = Column(Text, comment="结果说明")

    status = Column(String(20), default="draft", comment="状态：draft/preparing/submitted/closed")
    remark = Column(Text, comment="备注")

    # 关系
    customer = relationship("Customer", foreign_keys=[customer_id])
    sales_person = relationship("User", foreign_keys=[sales_person_id])
    support_person = relationship("User", foreign_keys=[support_person_id])
    documents = relationship("BiddingDocument", back_populates="bidding_project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_bidding_no", "bidding_no"),
        Index("idx_bidding_customer", "customer_id"),
        Index("idx_deadline", "deadline_date"),
        Index("idx_result", "bid_result"),
    )

    def __repr__(self):
        return f"<BiddingProject {self.bidding_no}>"


class BiddingDocument(Base, TimestampMixin):
    """投标文件表"""

    __tablename__ = "bidding_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bidding_project_id = Column(Integer, ForeignKey("bidding_projects.id"), nullable=False, comment="投标项目ID")
    document_type = Column(String(50), comment="文件类型：technical/commercial/qualification/other")
    document_name = Column(String(200), comment="文件名称")
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    version = Column(String(20), comment="版本号")
    status = Column(String(20), default="draft", comment="状态：draft/reviewed/approved")
    reviewed_by = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_at = Column(DateTime, comment="审核时间")
    remark = Column(Text, comment="备注")

    # 关系
    bidding_project = relationship("BiddingProject", back_populates="documents")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("idx_bidding_project", "bidding_project_id"),
        Index("idx_bidding_document_type", "document_type"),
    )

    def __repr__(self):
        return f"<BiddingDocument {self.document_name}>"
