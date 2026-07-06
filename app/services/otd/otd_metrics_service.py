# -*- coding: utf-8 -*-
"""
OTD 项目交付智能体 - 7 核心指标计算

7 个指标（对应符哥要求的核心指标）：
  1. 项目准时交付率   stage=S9 中 actual_end_date <= planned_end_date 占比
  2. 项目延期天数     已完成 (actual-planned).days；在途 (today-planned).days
  3. 返工次数(代理)   sum(AcceptanceOrderItem.retry_count) by project
  4. 变更次数         count(ChangeRequest) + count(Ecn) by project
  5. 项目毛利偏差     复用 ProfitAnalysisService 的 margin_gap 均值/分布
  6. 验收周期         avg((actual_end-actual_start).days) where status=COMPLETED
  7. 客户投诉率       count(feedback_type=COMPLAINT) / 项目数

代理口径（首版不改表）：
  - 返工：用 AcceptanceOrderItem.retry_count（验收复验次数）代替返工单
  - 图纸冻结（在 scan service 里）：用 DDR 评审通过代替

支持时间窗参数 start_date / end_date，默认本季度。
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.after_sales import AfterSalesFeedback
from app.models.change_request import ChangeRequest
from app.models.ecn.core import Ecn
from app.models.project import Project

logger = logging.getLogger(__name__)

# 已完结阶段（S9 = 验收交付/结项）
COMPLETED_STAGE = "S9"


def _quarter_range(today: date) -> tuple:
    """返回当前季度的起止日期。"""
    q = (today.month - 1) // 3 + 1
    start = date(today.year, (q - 1) * 3 + 1, 1)
    end = date(today.year, q * 3 + 1, 1) if q < 4 else date(today.year + 1, 1, 1)
    return start, end


class OTDMetricsService:
    """OTD 7 核心指标聚合"""

    def __init__(self, db: Session):
        self.db = db
        self._today = date.today()

    def get_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_offenders: bool = True,
    ) -> Dict[str, Any]:
        """
        聚合 7 核心指标。带 180s 缓存 + 可选下钻（top_offenders）。

        时间窗作用于：变更次数、客户投诉（按 created_at 过滤）。
        准时交付率/延期天数：基于已完结项目（stage=S9）的整体统计。
        返工/验收周期/毛利：基于时间窗内项目整体统计。
        """
        if not start_date or not end_date:
            start_date, end_date = _quarter_range(self._today)

        # 缓存（key 含时间窗 + 是否下钻）
        from app.utils.cache_decorator import get_cache_service

        cache = get_cache_service()
        cache_key = f"otd_metrics:{start_date}:{end_date}:{include_offenders}"
        cached = cache.get(cache_key)
        if cached is not None:
            cached["_from_cache"] = True
            return cached

        result = {
            "window": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "metrics": {
                "on_time_delivery_rate": self._on_time_delivery_rate(
                    include_offenders=include_offenders
                ),
                "delay_days": self._delay_days_distribution(
                    include_offenders=include_offenders
                ),
                "rework_count": self._rework_count(
                    include_offenders=include_offenders
                ),
                "change_count": self._change_count(
                    start_date, end_date, include_offenders=include_offenders
                ),
                "margin_deviation": self._margin_deviation(
                    include_offenders=include_offenders
                ),
                "acceptance_cycle_days": self._acceptance_cycle_days(
                    include_offenders=include_offenders
                ),
                "customer_complaint_rate": self._customer_complaint_rate(
                    start_date, end_date, include_offenders=include_offenders
                ),
            },
            "generated_at": datetime.now().isoformat(),
        }
        result["_from_cache"] = False
        cache.set(cache_key, result, expire_seconds=180)
        return result

    def get_project_metrics(self, project_id: int) -> Dict[str, Any]:
        """单项目指标。"""
        project = (
            self.db.query(Project).filter(Project.id == project_id).first()
        )
        if not project:
            return {"error": "项目不存在", "project_id": project_id}

        return {
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage,
            "metrics": {
                "on_time_delivery_rate": self._on_time_delivery_rate(project_id),
                "delay_days": self._delay_days_distribution(project_id),
                "rework_count": self._rework_count(project_id),
                "change_count": self._change_count(
                    date(self._today.year, 1, 1), self._today, project_id
                ),
                "margin_deviation": self._margin_deviation(project_id),
                "acceptance_cycle_days": self._acceptance_cycle_days(project_id),
                "customer_complaint_rate": self._customer_complaint_rate(
                    date(self._today.year, 1, 1), self._today, project_id
                ),
            },
            "generated_at": datetime.now().isoformat(),
        }

    # ================================================================
    # 1. 项目准时交付率
    # ================================================================

    def _on_time_delivery_rate(
        self, project_id: Optional[int] = None, include_offenders: bool = True
    ) -> Dict:
        """stage=S9 中 actual_end_date <= planned_end_date 占比。"""
        query = self.db.query(Project).filter(Project.stage == COMPLETED_STAGE)
        if project_id:
            query = query.filter(Project.id == project_id)

        completed = query.filter(Project.actual_end_date.isnot(None)).all()
        total = len(completed)
        on_time = sum(
            1
            for p in completed
            if p.planned_end_date
            and p.actual_end_date
            and p.actual_end_date <= p.planned_end_date
        )
        rate = round(on_time / total * 100, 2) if total else 0.0

        # 下钻：逾期完成的项目 Top 5（按延期天数降序）
        offenders = []
        if include_offenders:
            late = [
                p
                for p in completed
                if p.planned_end_date
                and p.actual_end_date
                and p.actual_end_date > p.planned_end_date
            ]
            late.sort(
                key=lambda p: (p.actual_end_date - p.planned_end_date).days,
                reverse=True,
            )
            offenders = [
                {
                    "project_id": p.id,
                    "project_code": p.project_code,
                    "project_name": p.project_name,
                    "delay_days": (p.actual_end_date - p.planned_end_date).days,
                    "planned_end": p.planned_end_date.isoformat(),
                    "actual_end": p.actual_end_date.isoformat(),
                }
                for p in late[:5]
            ]

        return {
            "on_time": on_time,
            "total_completed": total,
            "rate_pct": rate,
            "note": "已完成(stage=S9)项目中 actual_end_date <= planned_end_date 占比",
            "top_offenders": offenders,
        }

    # ================================================================
    # 2. 项目延期天数（均值/分布）
    # ================================================================

    def _delay_days_distribution(
        self, project_id: Optional[int] = None, include_offenders: bool = True
    ) -> Dict:
        """
        已完成：(actual-planned).days；在途：(today-planned).days（仅超期项目）。
        """
        query = self.db.query(Project)
        if project_id:
            query = query.filter(Project.id == project_id)

        # 已完成延期
        completed = query.filter(
            Project.stage == COMPLETED_STAGE,
            Project.actual_end_date.isnot(None),
            Project.planned_end_date.isnot(None),
        ).all()
        completed_delays = [
            (p.actual_end_date - p.planned_end_date).days
            for p in completed
            if p.actual_end_date and p.planned_end_date
        ]

        # 在途超期（未完结且已过计划交付日）
        in_progress = query.filter(
            Project.stage != COMPLETED_STAGE,
            Project.planned_end_date.isnot(None),
            Project.planned_end_date < self._today,
        ).all()
        in_progress_delays = [
            (self._today - p.planned_end_date).days
            for p in in_progress
            if p.planned_end_date
        ]

        all_delays = completed_delays + in_progress_delays
        avg_delay = round(sum(all_delays) / len(all_delays), 1) if all_delays else 0

        # 下钻：延期最久的项目 Top 5（已完成 + 在途合并，按天数降序）
        offenders = []
        if include_offenders:
            offender_list = []
            for p in completed:
                if p.actual_end_date and p.planned_end_date:
                    d = (p.actual_end_date - p.planned_end_date).days
                    if d > 0:
                        offender_list.append((p, d, "已完成"))
            for p in in_progress:
                if p.planned_end_date:
                    d = (self._today - p.planned_end_date).days
                    offender_list.append((p, d, "在途"))
            offender_list.sort(key=lambda x: x[1], reverse=True)
            offenders = [
                {
                    "project_id": p.id,
                    "project_code": p.project_code,
                    "project_name": p.project_name,
                    "delay_days": d,
                    "status": s,
                }
                for p, d, s in offender_list[:5]
            ]

        return {
            "avg_delay_days": avg_delay,
            "completed_overdue_count": len(completed_delays),
            "in_progress_overdue_count": len(in_progress_delays),
            "max_delay_days": max(all_delays) if all_delays else 0,
            "top_offenders": offenders,
        }

    # ================================================================
    # 3. 返工次数（代理：AcceptanceOrderItem.retry_count 之和）
    # ================================================================

    def _rework_count(
        self, project_id: Optional[int] = None, include_offenders: bool = True
    ) -> Dict:
        from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem

        query = (
            self.db.query(func.coalesce(func.sum(AcceptanceOrderItem.retry_count), 0))
            .join(AcceptanceOrder, AcceptanceOrderItem.order_id == AcceptanceOrder.id)
        )
        if project_id:
            query = query.filter(AcceptanceOrder.project_id == project_id)

        total_retry = int(query.scalar() or 0)

        # 项次数（retry_count > 0 的行数）
        item_query = (
            self.db.query(func.count(AcceptanceOrderItem.id))
            .join(AcceptanceOrder, AcceptanceOrderItem.order_id == AcceptanceOrder.id)
            .filter(AcceptanceOrderItem.retry_count > 0)
        )
        if project_id:
            item_query = item_query.filter(AcceptanceOrder.project_id == project_id)
        items_with_retry = int(item_query.scalar() or 0)

        # 下钻：返工最多的项目 Top 5（按 retry_count 之和降序）
        offenders = []
        if include_offenders:
            rework_rows = (
                self.db.query(
                    AcceptanceOrder.project_id,
                    func.sum(AcceptanceOrderItem.retry_count).label("total"),
                )
                .join(
                    AcceptanceOrder, AcceptanceOrderItem.order_id == AcceptanceOrder.id
                )
                .group_by(AcceptanceOrder.project_id)
                .having(func.sum(AcceptanceOrderItem.retry_count) > 0)
                .order_by(func.sum(AcceptanceOrderItem.retry_count).desc())
                .limit(5)
                .all()
            )
            pid_to_code = {
                p.id: (p.project_code, p.project_name)
                for p in self.db.query(Project).filter(
                    Project.id.in_([r[0] for r in rework_rows if r[0]])
                ).all()
            }
            offenders = [
                {
                    "project_id": pid,
                    "project_code": pid_to_code.get(pid, ("?", "?"))[0],
                    "project_name": pid_to_code.get(pid, ("?", "?"))[1],
                    "rework_count": int(total or 0),
                }
                for pid, total in rework_rows
                if pid
            ]

        return {
            "total_retry_count": total_retry,
            "items_with_retry": items_with_retry,
            "proxy": "用 AcceptanceOrderItem.retry_count（验收复验次数）代替返工单",
            "top_offenders": offenders,
        }

    # ================================================================
    # 4. 变更次数（ChangeRequest + Ecn，可分客户/内部）
    # ================================================================

    def _change_count(
        self,
        start: date,
        end: date,
        project_id: Optional[int] = None,
        include_offenders: bool = True,
    ) -> Dict:
        cr_query = self.db.query(ChangeRequest).filter(
            ChangeRequest.created_at >= start,
            ChangeRequest.created_at < end,
        )
        ecn_query = self.db.query(Ecn).filter(
            Ecn.created_at >= start,
            Ecn.created_at < end,
        )
        if project_id:
            cr_query = cr_query.filter(ChangeRequest.project_id == project_id)
            ecn_query = ecn_query.filter(Ecn.project_id == project_id)

        cr_all = cr_query.count()
        cr_customer = cr_query.filter(ChangeRequest.change_source == "CUSTOMER").count()
        ecn_all = ecn_query.count()

        # 下钻：变更最多的项目 Top 5（CR + ECN 合并计数）
        offenders = []
        if include_offenders:
            cr_rows = (
                self.db.query(
                    ChangeRequest.project_id, func.count(ChangeRequest.id)
                )
                .filter(
                    ChangeRequest.created_at >= start,
                    ChangeRequest.created_at < end,
                    ChangeRequest.project_id.isnot(None),
                )
                .group_by(ChangeRequest.project_id)
                .all()
            )
            ecn_rows = (
                self.db.query(Ecn.project_id, func.count(Ecn.id))
                .filter(
                    Ecn.created_at >= start,
                    Ecn.created_at < end,
                    Ecn.project_id.isnot(None),
                )
                .group_by(Ecn.project_id)
                .all()
            )
            merge: dict = {}
            for pid, cnt in list(cr_rows) + list(ecn_rows):
                merge[pid] = merge.get(pid, 0) + int(cnt)
            top = sorted(merge.items(), key=lambda x: x[1], reverse=True)[:5]
            pid_to_code = {
                p.id: (p.project_code, p.project_name)
                for p in self.db.query(Project).filter(
                    Project.id.in_([pid for pid, _ in top if pid])
                ).all()
            }
            offenders = [
                {
                    "project_id": pid,
                    "project_code": pid_to_code.get(pid, ("?", "?"))[0],
                    "project_name": pid_to_code.get(pid, ("?", "?"))[1],
                    "change_count": cnt,
                }
                for pid, cnt in top
                if pid
            ]

        return {
            "change_request_total": cr_all,
            "change_request_customer": cr_customer,
            "change_request_internal": cr_all - cr_customer,
            "ecn_total": ecn_all,
            "grand_total": cr_all + ecn_all,
            "top_offenders": offenders,
        }

    # ================================================================
    # 5. 项目毛利偏差（复用 ProfitAnalysisService 的 margin_gap）
    # ================================================================

    def _margin_deviation(
        self, project_id: Optional[int] = None, include_offenders: bool = True
    ) -> Dict:
        """复用 batch_margin_analysis（消除 N+1），按 gap 升序取毛利最差的 Top 5。"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        service = ProfitAnalysisService(self.db)
        analyses = service.batch_margin_analysis(
            project_ids=[project_id] if project_id else None
        )

        gaps = [
            float(a.get("margin_gap", 0))
            for a in analyses
            if a.get("margin_gap") is not None
        ]
        avg_gap = round(sum(gaps) / len(gaps), 2) if gaps else 0.0
        below_target = sum(1 for g in gaps if g < 0)
        seriously_below = sum(1 for g in gaps if g < -5)

        # 下钻：毛利最差的项目 Top 5（margin_gap 升序，最负在前）
        offenders = []
        if include_offenders:
            sorted_a = sorted(analyses, key=lambda a: float(a.get("margin_gap", 0)))
            offenders = [
                {
                    "project_id": a.get("project_id"),
                    "project_code": a.get("project_code"),
                    "project_name": a.get("project_name"),
                    "margin_gap": float(a.get("margin_gap", 0)),
                    "current_margin_rate": float(a.get("current_margin_rate", 0)),
                    "health": a.get("health"),
                }
                for a in sorted_a[:5]
            ]

        return {
            "avg_margin_gap_pct": avg_gap,
            "project_count": len(gaps),
            "below_target_count": below_target,
            "seriously_below_count": seriously_below,
            "note": "margin_gap = 当前毛利率 - 目标毛利率（负值=低于目标）",
            "top_offenders": offenders,
        }

    # ================================================================
    # 6. 验收周期（avg((actual_end-actual_start).days)）
    # ================================================================

    def _acceptance_cycle_days(
        self, project_id: Optional[int] = None, include_offenders: bool = True
    ) -> Dict:
        from app.models.acceptance import AcceptanceOrder

        query = self.db.query(AcceptanceOrder).filter(
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.actual_start_date.isnot(None),
            AcceptanceOrder.actual_end_date.isnot(None),
        )
        if project_id:
            query = query.filter(AcceptanceOrder.project_id == project_id)

        orders = query.all()
        cycles = [
            (o.actual_end_date - o.actual_start_date).days
            for o in orders
            if o.actual_start_date and o.actual_end_date
        ]
        avg_cycle = round(sum(cycles) / len(cycles), 1) if cycles else 0.0

        # 按 FAT/SAT/FINAL 分组
        by_type: Dict[str, List[int]] = {}
        for o in orders:
            t = o.acceptance_type or "UNKNOWN"
            if o.actual_start_date and o.actual_end_date:
                by_type.setdefault(t, []).append(
                    (o.actual_end_date - o.actual_start_date).days
                )
        avg_by_type = {
            t: round(sum(v) / len(v), 1) for t, v in by_type.items() if v
        }

        # 下钻：验收周期最长的项目 Top 5（按周期降序）
        offenders = []
        if include_offenders and orders:
            pid_cycle: dict = {}
            for o in orders:
                if o.actual_start_date and o.actual_end_date and o.project_id:
                    d = (o.actual_end_date - o.actual_start_date).days
                    # 同项目取最长周期
                    if o.project_id not in pid_cycle or d > pid_cycle[o.project_id][1]:
                        pid_cycle[o.project_id] = (o, d)
            top = sorted(pid_cycle.values(), key=lambda x: x[1], reverse=True)[:5]
            pid_to_code = {
                p.id: (p.project_code, p.project_name)
                for p in self.db.query(Project).filter(
                    Project.id.in_([o.project_id for o, _ in top if o.project_id])
                ).all()
            }
            offenders = [
                {
                    "project_id": o.project_id,
                    "project_code": pid_to_code.get(o.project_id, ("?", "?"))[0],
                    "project_name": pid_to_code.get(o.project_id, ("?", "?"))[1],
                    "cycle_days": d,
                    "acceptance_type": o.acceptance_type,
                }
                for o, d in top
            ]

        return {
            "avg_cycle_days": avg_cycle,
            "completed_acceptance_count": len(orders),
            "avg_by_type": avg_by_type,
            "top_offenders": offenders,
        }

    # ================================================================
    # 7. 客户投诉率（COMPLAINT 占比）
    # ================================================================

    def _customer_complaint_rate(
        self,
        start: date,
        end: date,
        project_id: Optional[int] = None,
        include_offenders: bool = True,
    ) -> Dict:
        query = self.db.query(AfterSalesFeedback).filter(
            AfterSalesFeedback.created_at >= start,
            AfterSalesFeedback.created_at < end,
        )
        if project_id:
            query = query.filter(AfterSalesFeedback.project_id == project_id)

        total_feedback = query.count()
        complaints = query.filter(
            AfterSalesFeedback.feedback_type == "COMPLAINT"
        ).count()

        rate = round(complaints / total_feedback * 100, 2) if total_feedback else 0.0

        # 下钻：有投诉的项目 Top 5（按投诉数降序）
        offenders = []
        if include_offenders:
            comp_rows = (
                self.db.query(
                    AfterSalesFeedback.project_id,
                    func.count(AfterSalesFeedback.id),
                )
                .filter(
                    AfterSalesFeedback.created_at >= start,
                    AfterSalesFeedback.created_at < end,
                    AfterSalesFeedback.feedback_type == "COMPLAINT",
                    AfterSalesFeedback.project_id.isnot(None),
                )
                .group_by(AfterSalesFeedback.project_id)
                .order_by(func.count(AfterSalesFeedback.id).desc())
                .limit(5)
                .all()
            )
            pid_to_code = {
                p.id: (p.project_code, p.project_name)
                for p in self.db.query(Project).filter(
                    Project.id.in_([r[0] for r in comp_rows if r[0]])
                ).all()
            }
            offenders = [
                {
                    "project_id": pid,
                    "project_code": pid_to_code.get(pid, ("?", "?"))[0],
                    "project_name": pid_to_code.get(pid, ("?", "?"))[1],
                    "complaint_count": int(cnt),
                }
                for pid, cnt in comp_rows
                if pid
            ]

        return {
            "complaint_count": complaints,
            "total_feedback": total_feedback,
            "complaint_rate_pct": rate,
            "note": "投诉数 / 售后反馈总数（时间窗内）",
            "top_offenders": offenders,
        }
