# -*- coding: utf-8 -*-
"""AI 产出反馈模型：记录人工对 AI 产出的采纳/驳回结论。

结果反馈环节的数据地基：没有采纳记录就没有采纳率，没有采纳率就无从校准。
append-only，同一产出可多次反馈（先驳回、修正后采纳），统计口径取最新一条。
"""
from sqlalchemy import Column, ForeignKey, Integer, JSON, String, Text

from app.models.base import Base, TimestampMixin

VERDICTS = ("ADOPTED", "REJECTED", "PARTIAL")


class AIOutputFeedback(Base, TimestampMixin):
    """AI 产出的人工反馈（采纳/驳回/部分采纳）。"""

    __tablename__ = "ai_output_feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    feature_key = Column(
        String(60), nullable=False, index=True,
        comment="AI 功能标识，如 presale_requirement_analysis/three_tier_quotation/negotiation_advice",
    )
    ref_type = Column(String(50), comment="产出对象类型，如 requirement_analysis/quotation/ai_job")
    ref_id = Column(Integer, index=True, comment="产出对象ID")
    verdict = Column(String(20), nullable=False, comment="结论: ADOPTED/REJECTED/PARTIAL")
    reason = Column(Text, comment="采纳/驳回原因")
    detail = Column(JSON, comment="补充信息（如修改了哪些字段）")
    created_by = Column(Integer, comment="反馈人ID")
