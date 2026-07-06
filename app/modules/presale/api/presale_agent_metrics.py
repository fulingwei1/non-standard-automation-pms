# -*- coding: utf-8 -*-
"""售前智能体埋点查询 API。

提供核心 KPI 聚合查询，对应方案里 6 个核心指标的已采集部分：
  - 方案初稿周期（solution_draft_time 均值/中位）
  - 报价周期（quote_time 均值/中位）
  - 智能体使用次数（按时间窗）
  - 步骤成功率（定位哪步经常失败）
  - 平均引用案例数（弹药库健康度）

待真实数据/业务闭环后可补：
  - 报价准确率（需 join projects.actual_cost，对比报价）
  - 项目毛利偏差（报价毛利 vs 实际毛利）
  - 销售转化率（is_converted 字段手动回填后）
"""
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.modules.presale.models.presale_agent_metric import PresaleAgentMetric
from app.models.user import User

router = APIRouter(prefix="/presale-agent", tags=["售前智能体埋点"])


def _time_window(days: int) -> datetime:
    return datetime.now() - timedelta(days=days)


@router.get("/metrics", summary="售前智能体核心 KPI 查询")
def get_presale_agent_metrics(
    days: int = Query(30, ge=1, le=365, description="统计时间窗（天），默认30天"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """聚合查询近 N 天的智能体 KPI。

    返回：
        total_runs / success_runs / success_rate
        avg_solution_draft_time / median_solution_draft_time（方案初稿周期）
        avg_quote_time / median_quote_time（报价周期）
        avg_cited_cases（平均引用案例数）
        step_failure_counts（各步骤失败次数，定位瓶颈）
        by_equipment（按设备类型分组的使用次数）
        recent_runs（最近 10 条记录）
    """
    since = _time_window(days)

    base = db.query(PresaleAgentMetric).filter(PresaleAgentMetric.created_at >= since)

    total = base.count()
    success = base.filter(PresaleAgentMetric.status == "SUCCESS").count()
    success_rate = round(success / total, 4) if total else 0.0

    # 耗时统计（仅成功记录，失败的耗时无意义）
    def _time_stats(field):
        rows = (
            base.filter(PresaleAgentMetric.status == "SUCCESS", field.isnot(None))
            .with_entities(field)
            .all()
        )
        vals = sorted(float(r[0]) for r in rows if r[0] is not None)
        if not vals:
            return {"avg": None, "median": None, "p90": None, "samples": 0}
        return {
            "avg": round(sum(vals) / len(vals), 2),
            "median": round(vals[len(vals) // 2], 2),
            "p90": round(vals[int(len(vals) * 0.9)], 2) if len(vals) > 1 else round(vals[0], 2),
            "samples": len(vals),
        }

    draft_stats = _time_stats(PresaleAgentMetric.solution_draft_time)
    quote_stats = _time_stats(PresaleAgentMetric.quote_time)
    total_stats = _time_stats(PresaleAgentMetric.total_time)

    # 平均引用案例数
    cited_rows = base.filter(PresaleAgentMetric.status == "SUCCESS").with_entities(
        func.avg(PresaleAgentMetric.cited_case_count)
    ).all()
    avg_cited = round(float(cited_rows[0][0]), 2) if cited_rows and cited_rows[0][0] else 0.0

    # 各设备类型使用次数
    by_eq = db.execute(
        text(
            "SELECT equipment_type, COUNT(*) as cnt FROM presale_agent_metrics "
            "WHERE created_at >= :since AND equipment_type IS NOT NULL "
            "GROUP BY equipment_type ORDER BY cnt DESC LIMIT 10"
        ),
        {"since": since},
    ).all()

    # 最近 10 条记录
    recent = (
        db.query(PresaleAgentMetric)
        .order_by(PresaleAgentMetric.id.desc())
        .limit(10)
        .all()
    )

    return {
        "time_window_days": days,
        "since": since.isoformat(),
        "usage": {
            "total_runs": total,
            "success_runs": success,
            "success_rate": success_rate,
        },
        "solution_draft_time_s": draft_stats,
        "quote_time_s": quote_stats,
        "total_time_s": total_stats,
        "avg_cited_cases": avg_cited,
        "by_equipment": [{"equipment_type": r[0], "count": r[1]} for r in by_eq],
        "recent_runs": [r.to_dict() for r in recent],
    }
