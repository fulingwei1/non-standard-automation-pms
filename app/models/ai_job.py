# -*- coding: utf-8 -*-
"""AI 后台生成任务模型。

用于把耗时的 AI 生成（如三档报价、方案生成）从同步 HTTP 改为后台任务 + 轮询，
避免长调用占住请求/被浏览器或网关超时中断。
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text

from app.models.base import Base, TimestampMixin


class AIGenerationJob(Base, TimestampMixin):
    """AI 生成任务（后台执行，客户端轮询状态）。"""

    __tablename__ = "ai_generation_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    job_type = Column(String(50), nullable=False, comment="任务类型，如 three_tier_quotation")
    status = Column(
        String(20), default="PENDING", nullable=False,
        comment="状态: PENDING/RUNNING/SUCCESS/FAILED",
    )
    params = Column(JSON, comment="任务入参")
    result = Column(JSON, comment="任务结果")
    error = Column(Text, comment="失败原因")
    progress = Column(Integer, default=0, comment="进度 0-100")
    created_by = Column(Integer, comment="创建人ID")
    started_at = Column(DateTime, comment="开始执行时间")
    finished_at = Column(DateTime, comment="完成时间")
