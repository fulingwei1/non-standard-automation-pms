# -*- coding: utf-8 -*-
"""
售前智能体结果修订记录模型。

记录售前工程师对 AI 产出的修改，用于：
  1. 追溯：每次 AI 结果被谁改了什么、为什么改
  2. 改进：统计高频被改的字段，反哺 prompt/工具优化（"AI 越用越准"的核心闭环）

一条 revision = 一次智能体结果的定稿。
fields_diff 记录字段级差异：[{field, old_value, new_value, reason}]
"""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.models.base import Base


class PresaleAgentRevision(Base):
    """售前智能体结果修订记录"""

    __tablename__ = "presale_agent_revisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 关联到本次智能体运行（presale_agent_metrics.id 或 ai_generation_jobs.id）
    metric_id = Column(Integer, comment="关联 presale_agent_metrics.id")
    job_id = Column(Integer, comment="关联 ai_generation_jobs.id")
    # 原始需求
    requirement_text = Column(Text, comment="原始客户需求")
    # AI 原稿（完整 result JSON）
    ai_output = Column(JSON, comment="AI 原始产出（完整 result）")
    # 工程师定稿（修改后的完整 result）
    revised_output = Column(JSON, comment="工程师定稿（修改后）")
    # 字段级 diff（核心：哪些字段被改了）
    fields_diff = Column(
        JSON,
        comment="字段差异列表 [{section, field, old_value, new_value, reason}]",
    )
    # 修订元信息
    revised_by = Column(Integer, comment="修订人ID（售前工程师）")
    revised_by_name = Column(String(100), comment="修订人姓名")
    revision_note = Column(Text, comment="整体修订说明")
    # 改动规模（用于快速筛"大改/小改"）
    changed_field_count = Column(Integer, default=0, comment="被修改的字段数")
    is_major_revision = Column(
        Integer, default=0, comment="是否大改（0小改1大改，便于筛选重点复盘）"
    )
    # 状态：草稿 / 已确认
    status = Column(String(20), default="CONFIRMED", comment="DRAFT/CONFIRMED")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<PresaleAgentRevision {self.id}: metric={self.metric_id} changes={self.changed_field_count}>"

    def to_dict(self):
        return {
            "id": self.id,
            "metric_id": self.metric_id,
            "job_id": self.job_id,
            "requirement_text": (self.requirement_text or "")[:120],
            "changed_field_count": self.changed_field_count,
            "is_major_revision": self.is_major_revision,
            "fields_diff": self.fields_diff,
            "revised_by_name": self.revised_by_name,
            "revision_note": self.revision_note,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
