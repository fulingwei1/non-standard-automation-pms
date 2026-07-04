# -*- coding: utf-8 -*-
"""售前智能体运行埋点模型。

每次智能体分析（POST /ai-jobs/presale-agent）落一条记录，用于统计：
  - 方案初稿周期（understand + retrieve + generate_solution 三步耗时）
  - 报价周期（全部 6 步耗时 = total_time）
  - 智能体使用次数 / 活跃用户
  - 各步骤成功率（定位哪步经常失败）
  - 引用案例数（弹药库健康度）

后续可补：报价→实际成交偏差（需 join projects.actual_cost，等真实数据）、
        是否转化为签单（is_converted，需手动回填或外接 CRM）。
"""
from sqlalchemy import JSON, Column, DateTime, Integer, Numeric, String, Text

from app.models.base import Base, TimestampMixin


class PresaleAgentMetric(Base, TimestampMixin):
    """售前智能体单次运行埋点"""

    __tablename__ = "presale_agent_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, comment="关联 ai_generation_jobs.id")
    created_by = Column(Integer, comment="发起人ID")

    # 需求侧
    requirement_text = Column(Text, comment="原始需求（截断存储，便于复盘）")
    industry = Column(String(100), comment="AI 解析出的行业")
    equipment_type = Column(String(100), comment="AI 解析出的设备类型")

    # 耗时埋点（秒）—— 对应核心 KPI
    total_time = Column(Numeric(8, 2), comment="总耗时（=报价周期上限）")
    solution_draft_time = Column(
        Numeric(8, 2),
        comment="方案初稿周期 = 需求理解+弹药检索+方案生成 三步耗时之和",
    )
    quote_time = Column(
        Numeric(8, 2),
        comment="报价周期 = 从启动到 quote_range 步完成（含前面所有步）",
    )

    # 步骤成功标志（定位哪步经常失败）
    steps_ok = Column(JSON, comment="{step_key: bool} 各步骤是否成功")

    # 弹药库健康度指标
    cited_case_count = Column(Integer, comment="本次引用的历史案例数")
    quote_sample_count = Column(Integer, comment="报价区间命中样本数")

    # 最终状态
    status = Column(String(20), comment="SUCCESS/FAILED")
    error = Column(Text, comment="失败原因（FAILED 时填）")

    # 业务结果（后续手动回填）
    is_converted = Column(Integer, comment="是否转化为签单（0/1，后续回填）")
    actual_project_id = Column(Integer, comment="实际立项的项目ID（后续回填）")

    def __repr__(self):
        return f"<PresaleAgentMetric {self.id}: job={self.job_id} {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "created_by": self.created_by,
            "requirement_text": (self.requirement_text or "")[:120],
            "industry": self.industry,
            "equipment_type": self.equipment_type,
            "total_time": float(self.total_time) if self.total_time else None,
            "solution_draft_time": float(self.solution_draft_time)
            if self.solution_draft_time
            else None,
            "quote_time": float(self.quote_time) if self.quote_time else None,
            "steps_ok": self.steps_ok,
            "cited_case_count": self.cited_case_count,
            "quote_sample_count": self.quote_sample_count,
            "status": self.status,
            "error": self.error,
            "is_converted": self.is_converted,
            "actual_project_id": self.actual_project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
