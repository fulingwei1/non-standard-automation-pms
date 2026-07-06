# -*- coding: utf-8 -*-
"""
验厂资料请求模型。

流程：销售提交请求 → 销售总监审批 → 通过后 AI 自动生成验厂资料包 HTML。
状态机：pending（待审批）→ approved（已通过，生成资料包）/ rejected（拒绝）
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.models.base import Base


class AuditPackRequest(Base):
    """验厂资料请求"""

    __tablename__ = "audit_pack_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 请求信息
    customer_name = Column(String(200), nullable=False, comment="客户名称")
    customer_industry = Column(String(100), comment="客户行业")
    project_name = Column(String(200), comment="关联项目名")
    audit_purpose = Column(Text, comment="验厂目的/客户要求")
    checklist_text = Column(Text, comment="客户验厂清单内容（文本）")
    checklist_file = Column(String(500), nullable=True, comment="清单文件路径")
    special_requirements = Column(Text, nullable=True, comment="特殊要求")
    deadline = Column(String(50), comment="截止日期")
    # 状态
    status = Column(String(20), default="pending", comment="pending/approved/rejected")
    # 提交人
    submitted_by = Column(Integer, comment="提交人ID（销售）")
    submitted_by_name = Column(String(100), comment="提交人姓名")
    # 审批
    reviewed_by = Column(Integer, nullable=True, comment="审批人ID（销售总监）")
    reviewed_by_name = Column(String(100), nullable=True, comment="审批人姓名")
    reviewed_at = Column(DateTime, nullable=True, comment="审批时间")
    review_comment = Column(Text, nullable=True, comment="审批意见")
    # 生成的资料包
    generated_html = Column(Text, nullable=True, comment="AI 生成的验厂资料包 HTML")
    generated_at = Column(DateTime, nullable=True, comment="生成时间")
    # 时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_industry": self.customer_industry,
            "project_name": self.project_name,
            "audit_purpose": (self.audit_purpose or "")[:100],
            "special_requirements": (self.special_requirements or "")[:100],
            "deadline": self.deadline,
            "status": self.status,
            "submitted_by_name": self.submitted_by_name,
            "reviewed_by_name": self.reviewed_by_name,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_comment": self.review_comment,
            "has_html": bool(self.generated_html),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
