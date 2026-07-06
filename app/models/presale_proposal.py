# -*- coding: utf-8 -*-
"""
售前方案协作模型。

记录方案的迭代版本链 + 协作状态机：
  draft（迭代中，销售/任何人和 agent 互动修改）
  → pending_review（销售提交审核）
  → approved（工程师通过，定稿）/ rejected（打回，回到 draft）

一个 proposal = 一次售前智能体分析产出的方案，可以有多个 version（每次修改一个版本）。
每次 version 记录：谁、提了什么建议、agent 改了什么、完整方案 JSON。
"""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.models.base import Base


class PresaleProposal(Base):
    """售前方案（一次智能体分析 = 一个 proposal，含多轮迭代）"""

    __tablename__ = "presale_proposals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="方案标题（取自需求）")
    requirement_text = Column(Text, nullable=False, comment="原始客户需求")
    # 当前方案内容（最新版本的完整 JSON，含 steps）
    current_solution = Column(JSON, comment="当前方案内容（最新版本完整JSON）")
    # 状态机：draft/pending_review/approved/rejected
    status = Column(String(20), default="draft", comment="draft/pending_review/approved/rejected")
    # 关联的智能体运行
    metric_id = Column(Integer, nullable=True, comment="关联 presale_agent_metrics.id")
    # 创建/负责人
    created_by = Column(Integer, comment="创建人（发起需求的销售）")
    created_by_name = Column(String(100), comment="创建人姓名")
    # 审核信息
    reviewed_by = Column(Integer, nullable=True, comment="审核人（售前工程师）")
    reviewed_by_name = Column(String(100), nullable=True, comment="审核人姓名")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    review_comment = Column(Text, nullable=True, comment="审核意见（通过/打回理由）")
    # 迭代计数
    version_count = Column(Integer, default=1, comment="迭代版本数")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "requirement_text": (self.requirement_text or "")[:120],
            "status": self.status,
            "created_by_name": self.created_by_name,
            "reviewed_by_name": self.reviewed_by_name,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_comment": self.review_comment,
            "version_count": self.version_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PresaleProposalVersion(Base):
    """方案迭代版本（每一轮修改 = 一个 version）"""

    __tablename__ = "presale_proposal_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(Integer, nullable=False, comment="关联 presale_proposals.id")
    version_no = Column(Integer, nullable=False, comment="版本号（1=初稿，2,3...=迭代）")
    # 这轮的修改建议（销售/用户提的）
    change_request = Column(Text, comment="用户提的修改建议")
    # agent 理解后改了什么（字段级摘要）
    changes_summary = Column(Text, comment="agent 本次修改摘要（改了哪些部分）")
    # 完整方案 JSON（这轮修改后的）
    solution = Column(JSON, comment="本版本完整方案JSON")
    # 操作人
    operated_by = Column(Integer, comment="操作人ID")
    operated_by_name = Column(String(100), comment="操作人姓名")
    operation = Column(String(20), comment="create/revise/submit/approve/reject")
    created_at = Column(DateTime, default=datetime.now)
