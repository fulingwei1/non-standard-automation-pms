# -*- coding: utf-8 -*-
"""
销售漏斗优化服务

将漏斗转化率、瓶颈、健康度、趋势分析从 endpoint 中剥离，
并用真实业务数据替换原有的伪波动/写死趋势逻辑。
"""

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from app.common.date_range import get_month_range_by_ym
from app.core.sales_permissions import filter_sales_data_by_scope
from app.models.enums.sales import OpportunityStageEnum
from app.models.sales import FunnelTransitionLog, Opportunity
from app.models.user import User
from app.services.sales_forecast_service import SalesForecastService


STAGE_DISPLAY_NAMES = {
    OpportunityStageEnum.DISCOVERY: "初步接触",
    OpportunityStageEnum.QUALIFICATION: "需求挖掘",
    OpportunityStageEnum.PROPOSAL: "方案介绍",
    OpportunityStageEnum.NEGOTIATION: "价格谈判",
    OpportunityStageEnum.CLOSING: "成交促成",
    OpportunityStageEnum.WON: "赢单",
    OpportunityStageEnum.LOST: "输单",
}

BENCHMARK_CONVERSION_RATES = {
    OpportunityStageEnum.DISCOVERY: 65.0,
    OpportunityStageEnum.QUALIFICATION: 60.0,
    OpportunityStageEnum.PROPOSAL: 70.0,
    OpportunityStageEnum.NEGOTIATION: 65.0,
    OpportunityStageEnum.CLOSING: 80.0,
}

BENCHMARK_DAYS_IN_STAGE = {
    OpportunityStageEnum.DISCOVERY: 7.0,
    OpportunityStageEnum.QUALIFICATION: 14.0,
    OpportunityStageEnum.PROPOSAL: 21.0,
    OpportunityStageEnum.NEGOTIATION: 14.0,
    OpportunityStageEnum.CLOSING: 7.0,
}


class SalesFunnelOptimizationService:
    """销售漏斗优化分析服务。"""

    FUNNEL_STAGES = [
        OpportunityStageEnum.DISCOVERY,
        OpportunityStageEnum.QUALIFICATION,
        OpportunityStageEnum.PROPOSAL,
        OpportunityStageEnum.NEGOTIATION,
        OpportunityStageEnum.CLOSING,
        OpportunityStageEnum.WON,
    ]
    ACTIVE_PIPELINE_STAGES = FUNNEL_STAGES[:-1]
    DEFAULT_STAGE_PROBABILITIES = {
        OpportunityStageEnum.DISCOVERY: 25.0,
        OpportunityStageEnum.QUALIFICATION: 45.0,
        OpportunityStageEnum.PROPOSAL: 65.0,
        OpportunityStageEnum.NEGOTIATION: 80.0,
        OpportunityStageEnum.CLOSING: 90.0,
    }

    ROOT_CAUSES_BY_STAGE = {
        OpportunityStageEnum.DISCOVERY.value: [
            "客户需求不清晰，难以判断项目可行性",
            "目标客户定位不准确",
            "线索质量参差不齐",
        ],
        OpportunityStageEnum.QUALIFICATION.value: [
            "需求调研不够系统化",
            "客户配合度低，信息获取困难",
            "技术可行性评估耗时长",
        ],
        OpportunityStageEnum.PROPOSAL.value: [
            "方案设计周期长",
            "技术方案反复修改",
            "售前资源不足",
        ],
        OpportunityStageEnum.NEGOTIATION.value: [
            "价格异议处理能力不足",
            "价值传递不够清晰",
            "决策链渗透不够深入",
            "竞品价格冲击",
        ],
        OpportunityStageEnum.CLOSING.value: [
            "合同条款反复确认",
            "客户采购流程推进缓慢",
            "回款与交付条件未达成一致",
        ],
    }

    RECOMMENDATIONS_BY_STAGE = {
        OpportunityStageEnum.DISCOVERY.value: [
            "建立标准化的客户初筛清单",
            "加强线索来源质量管控",
            "优化首次沟通话术",
        ],
        OpportunityStageEnum.QUALIFICATION.value: [
            "使用标准化需求调研模板",
            "设定明确的客户反馈截止时间",
            "提前准备 2-3 套备选方案",
        ],
        OpportunityStageEnum.PROPOSAL.value: [
            "建立方案模板库，提高复用率",
            "加强售前工程师培训",
            "优化内部方案评审流程",
        ],
        OpportunityStageEnum.NEGOTIATION.value: [
            "加强价格谈判培训",
            "准备 TCO（总拥有成本）分析工具",
            "提前识别并接触技术/采购决策人",
            "提供分期付款方案降低门槛",
        ],
        OpportunityStageEnum.CLOSING.value: [
            "提前梳理合同关键条款清单",
            "联合商务和法务并行推进审批",
            "为客户采购流程设置里程碑跟催",
        ],
    }

    def __init__(self, db: Session):
        self.db = db
        self.forecast_service = SalesForecastService(db)

    def get_conversion_rates(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sales_id: Optional[int] = None,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """获取销售漏斗转化率与阶段停留分析。"""
        start_dt, end_dt = self._resolve_date_range(start_date, end_date)
        current_snapshot = self._build_conversion_snapshot(
            start_dt=start_dt,
            end_dt=end_dt,
            sales_id=sales_id,
            current_user=current_user,
        )
        previous_start, previous_end = self._get_previous_period(start_dt, end_dt)
        previous_snapshot = self._build_conversion_snapshot(
            start_dt=previous_start,
            end_dt=previous_end,
            sales_id=sales_id,
            current_user=current_user,
        )

        stages_data = []
        for stage in self.FUNNEL_STAGES:
            current_stage_metrics = current_snapshot["stage_metrics"][stage]
            previous_stage_metrics = previous_snapshot["stage_metrics"].get(stage, {})
            stages_data.append(
                {
                    "stage": stage.value,
                    "stage_name": STAGE_DISPLAY_NAMES.get(stage, stage.value),
                    "count": current_stage_metrics["count"],
                    "conversion_to_next": current_stage_metrics["conversion_to_next"],
                    "avg_days_in_stage": current_stage_metrics["avg_days_in_stage"],
                    "trend": self._resolve_stage_trend(
                        current_stage_metrics=current_stage_metrics,
                        previous_stage_metrics=previous_stage_metrics,
                    ),
                }
            )

        overall_metrics = current_snapshot["overall_metrics"].copy()
        overall_metrics.update(current_snapshot["pipeline_metrics"])

        return {
            "period": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
            },
            "stages": stages_data,
            "overall_metrics": overall_metrics,
        }

    def get_bottlenecks(
        self,
        threshold: float = 55.0,
        current_user: Optional[User] = None,
        sales_id: Optional[int] = None,
        start_dt: Optional[date] = None,
        end_dt: Optional[date] = None,
    ) -> Dict[str, Any]:
        """识别销售漏斗瓶颈。"""
        analysis_end = end_dt or date.today()
        analysis_start = start_dt or (analysis_end - timedelta(days=90))
        conversion_data = self.get_conversion_rates(
            start_date=analysis_start.isoformat(),
            end_date=analysis_end.isoformat(),
            sales_id=sales_id,
            current_user=current_user,
        )
        return self._build_bottleneck_payload(
            conversion_data=conversion_data,
            threshold=threshold,
            analysis_date=analysis_end,
        )

    def get_prediction_accuracy(
        self,
        months: int = 3,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """分析赢单预测准确性。"""
        end_dt = date.today()
        start_dt = end_dt - timedelta(days=months * 30)
        closed_opps = self._get_closed_opportunities(
            start_dt=start_dt,
            end_dt=end_dt,
            current_user=current_user,
        )
        total_opps = len(closed_opps)
        won_opps = [opp for opp in closed_opps if opp.stage == OpportunityStageEnum.WON.value]

        if total_opps == 0:
            return {
                "period": {"months": months, "total_opportunities": 0, "closed_opportunities": 0},
                "overall_accuracy": {
                    "predicted_win_rate": 0,
                    "actual_win_rate": 0,
                    "accuracy_score": 0,
                    "bias": "数据不足",
                },
                "by_stage": [],
                "over_optimistic": [],
                "recommendations": ["数据量不足，建议积累更多历史数据后再分析"],
            }

        actual_win_rate = round(len(won_opps) / total_opps * 100, 1)
        total_predicted = sum((opp.probability or 50) for opp in closed_opps)
        predicted_win_rate = round(total_predicted / total_opps, 1)

        accuracy_score = round(100 - abs(predicted_win_rate - actual_win_rate), 1)
        accuracy_score = max(0, min(100, accuracy_score))

        diff = predicted_win_rate - actual_win_rate
        if abs(diff) < 5:
            bias = "准确"
        elif diff > 0:
            bias = "乐观" if diff < 15 else "过度乐观"
        else:
            bias = "保守" if diff > -15 else "过度保守"

        stage_analysis = self._build_prediction_accuracy_by_stage(
            closed_opps=closed_opps,
            overall_actual_win_rate=actual_win_rate,
        )

        over_optimistic = []
        lost_opps = [
            opp for opp in closed_opps if opp.stage == OpportunityStageEnum.LOST.value
        ]
        for opp in sorted(lost_opps, key=lambda item: item.probability or 0, reverse=True)[:5]:
            probability = opp.probability or 50
            if probability >= 60:
                over_optimistic.append(
                    {
                        "opportunity_id": opp.id,
                        "opportunity_name": opp.opp_name,
                        "predicted_rate": probability,
                        "actual_outcome": "LOST",
                        "gap": -probability,
                        "reason": "需复盘分析输单原因",
                    }
                )

        recommendations = []
        for stage in stage_analysis:
            if stage["bias"] == "乐观" and stage.get("accuracy") is not None and stage["accuracy"] < 85:
                recommendations.append(
                    f"{stage['stage_name']} 阶段预测偏乐观（预测{stage['predicted']}% vs 实际{stage['actual']}%），建议加入更多客观评分因素"
                )
        if diff > 10:
            recommendations.append("整体预测偏乐观，建议建立预测复盘机制，每月分析偏差原因")
        if not recommendations:
            recommendations.append("预测准确性良好，建议继续保持并定期校准")

        return {
            "period": {
                "months": months,
                "total_opportunities": total_opps,
                "closed_opportunities": total_opps,
            },
            "overall_accuracy": {
                "predicted_win_rate": predicted_win_rate,
                "actual_win_rate": actual_win_rate,
                "accuracy_score": accuracy_score,
                "bias": bias,
            },
            "by_stage": stage_analysis,
            "over_optimistic": over_optimistic[:3],
            "recommendations": recommendations[:3],
        }

    def get_health_dashboard(
        self,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """获取漏斗健康度仪表盘。"""
        today = date.today()
        current_bottleneck_data = self.get_bottlenecks(
            threshold=55.0,
            current_user=current_user,
            start_dt=today - timedelta(days=90),
            end_dt=today,
        )
        conversion_data = self.get_conversion_rates(
            start_date=(today - timedelta(days=30)).isoformat(),
            end_date=today.isoformat(),
            sales_id=None,
            current_user=current_user,
        )

        previous_start, previous_end = self._get_previous_period(
            today - timedelta(days=90),
            today,
        )
        previous_bottleneck_data = self.get_bottlenecks(
            threshold=55.0,
            current_user=current_user,
            start_dt=previous_start,
            end_dt=previous_end,
        )

        metrics = conversion_data.get("overall_metrics", {})
        health_score = current_bottleneck_data.get("overall_health_score", 70)
        previous_health_score = previous_bottleneck_data.get("overall_health_score", 70)

        if health_score >= 80:
            level = "EXCELLENT"
        elif health_score >= 60:
            level = "GOOD"
        elif health_score >= 40:
            level = "FAIR"
        else:
            level = "POOR"

        monthly_target = self.forecast_service._get_sales_target(today.year, today.month, "monthly")
        target_source = self.forecast_service._get_target_source(today.year, today.month, "monthly")
        weighted_pipeline = float(metrics.get("weighted_pipeline_value", 0) or 0)
        target_coverage = round((weighted_pipeline / monthly_target) * 100, 1) if monthly_target > 0 else 0.0

        alerts = []
        for bottleneck in current_bottleneck_data.get("bottlenecks", [])[:2]:
            alerts.append(
                {
                    "type": "WARNING",
                    "title": (
                        f"{bottleneck['stage_name']} "
                        f"{'转化率偏低' if bottleneck['issue_type'] == 'low_conversion' else '停留时间过长'}"
                    ),
                    "description": bottleneck.get("impact", ""),
                    "action": "查看瓶颈分析",
                }
            )

        if monthly_target <= 0:
            alerts.append(
                {
                    "type": "INFO",
                    "title": "未配置月度目标",
                    "description": "当前月份未找到销售目标，覆盖率按 0% 展示",
                    "action": "维护销售目标",
                }
            )
        elif target_coverage >= 100:
            alerts.append(
                {
                    "type": "SUCCESS" if target_coverage >= 120 else "INFO",
                    "title": "Pipeline 充足" if target_coverage >= 120 else "Pipeline 达标",
                    "description": f"当前 Pipeline 覆盖月度目标的 {target_coverage}%",
                    "action": None,
                }
            )
        else:
            alerts.append(
                {
                    "type": "WARNING",
                    "title": "Pipeline 不足",
                    "description": f"当前 Pipeline 仅覆盖月度目标的 {target_coverage}%",
                    "action": "增加线索获取",
                }
            )

        top_actions = []
        priority = 1
        for bottleneck in current_bottleneck_data.get("bottlenecks", []):
            if bottleneck["severity"] == "HIGH":
                top_actions.append(
                    {
                        "priority": priority,
                        "action": (
                            f"解决 {bottleneck['stage_name']} 阶段的"
                            f"{'低转化率' if bottleneck['issue_type'] == 'low_conversion' else '长停留'}问题"
                        ),
                        "impact": bottleneck.get("impact", ""),
                    }
                )
                priority += 1
            if priority > 3:
                break

        avg_cycle = float(metrics.get("avg_sales_cycle_days", 0) or 0)
        pipeline_count = int(metrics.get("pipeline_opportunity_count", 0) or 0)

        return {
            "dashboard_date": today.isoformat(),
            "overall_health": {
                "score": health_score,
                "level": level,
                "trend": self._resolve_score_trend(health_score, previous_health_score),
            },
            "key_metrics": {
                "total_pipeline": float(metrics.get("total_pipeline_value", 0) or 0),
                "weighted_pipeline": weighted_pipeline,
                "monthly_target": round(monthly_target, 2),
                "target_coverage": target_coverage,
                "target_source": target_source,
                "avg_deal_size": round(
                    float(metrics.get("total_pipeline_value", 0) or 0) / max(pipeline_count, 1),
                    1,
                ) if pipeline_count > 0 else 0.0,
                "sales_velocity": round(weighted_pipeline / avg_cycle, 1) if avg_cycle > 0 else 0.0,
            },
            "alerts": alerts[:3],
            "top_actions": top_actions[:3],
        }

    def get_trends(
        self,
        period: str = "monthly",
        months: int = 6,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """获取销售漏斗趋势分析。"""
        end_dt = date.today()
        trends_data = []

        for year, month in self._iter_recent_months(max(1, months), end_dt):
            month_start, month_end = get_month_range_by_ym(year, month)
            bucket_end = min(month_end, end_dt)
            month_opps = self._get_opportunities(
                start_dt=month_start,
                end_dt=bucket_end,
                sales_id=None,
                current_user=current_user,
            )
            stage_counts = self._build_stage_counts(month_opps)
            leads = stage_counts[OpportunityStageEnum.DISCOVERY]
            won = stage_counts[OpportunityStageEnum.WON]

            trends_data.append(
                {
                    "period": f"{year}-{month:02d}",
                    "leads": leads,
                    "stage2": stage_counts[OpportunityStageEnum.QUALIFICATION],
                    "stage3": stage_counts[OpportunityStageEnum.PROPOSAL],
                    "stage4": stage_counts[OpportunityStageEnum.NEGOTIATION],
                    "stage5": stage_counts[OpportunityStageEnum.CLOSING],
                    "won": won,
                    "conversion_rate": round((won / leads * 100), 1) if leads > 0 else 0.0,
                }
            )

        insights = []
        if len(trends_data) >= 2:
            first_leads = trends_data[0]["leads"]
            last_leads = trends_data[-1]["leads"]
            if first_leads > 0:
                growth = round((last_leads - first_leads) / first_leads * 100, 1)
                if growth > 0:
                    insights.append(f"线索量增长 {growth}%")
                elif growth < 0:
                    insights.append(f"线索量下降 {abs(growth)}%")

            avg_conversion = sum(item["conversion_rate"] for item in trends_data) / len(trends_data)
            insights.append(f"平均转化率 {round(avg_conversion, 1)}%")

        return {
            "period": period,
            "months": months,
            "data": trends_data,
            "insights": insights or ["数据收集中..."],
        }

    def _resolve_date_range(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> tuple[date, date]:
        start_dt = date.fromisoformat(start_date) if start_date else date.today() - timedelta(days=90)
        end_dt = date.fromisoformat(end_date) if end_date else date.today()
        return start_dt, end_dt

    def _build_conversion_snapshot(
        self,
        start_dt: date,
        end_dt: date,
        sales_id: Optional[int],
        current_user: Optional[User],
    ) -> Dict[str, Any]:
        opportunities = self._get_opportunities(
            start_dt=start_dt,
            end_dt=end_dt,
            sales_id=sales_id,
            current_user=current_user,
        )
        stage_counts = self._build_stage_counts(opportunities)
        stage_metrics: Dict[OpportunityStageEnum, Dict[str, Any]] = {}

        prev_count: Optional[int] = None
        for stage in self.FUNNEL_STAGES:
            count = stage_counts[stage]
            if prev_count is not None and prev_count > 0:
                conversion_to_next = round((count / prev_count) * 100, 1)
            else:
                conversion_to_next = None if stage == OpportunityStageEnum.WON else 100.0

            stage_metrics[stage] = {
                "count": count,
                "conversion_to_next": conversion_to_next,
                "avg_days_in_stage": self._calculate_avg_days_in_stage(
                    stage=stage,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    sales_id=sales_id,
                    current_user=current_user,
                ),
            }
            prev_count = count

        total_leads = stage_counts[OpportunityStageEnum.DISCOVERY]
        total_won = stage_counts[OpportunityStageEnum.WON]
        won_opportunities = [
            opp for opp in opportunities if opp.stage == OpportunityStageEnum.WON.value
        ]

        return {
            "stage_metrics": stage_metrics,
            "overall_metrics": {
                "total_leads": total_leads,
                "total_won": total_won,
                "overall_conversion_rate": round((total_won / total_leads) * 100, 1)
                if total_leads > 0 else 0.0,
                "avg_sales_cycle_days": self._calculate_avg_sales_cycle_days(won_opportunities),
            },
            "pipeline_metrics": self._calculate_pipeline_metrics(opportunities),
        }

    def _get_opportunities(
        self,
        start_dt: date,
        end_dt: date,
        sales_id: Optional[int],
        current_user: Optional[User],
    ) -> List[Opportunity]:
        start_at = datetime.combine(start_dt, time.min)
        end_exclusive = datetime.combine(end_dt + timedelta(days=1), time.min)
        query = self.db.query(Opportunity).filter(
            Opportunity.created_at >= start_at,
            Opportunity.created_at < end_exclusive,
        )
        if current_user is not None:
            query = filter_sales_data_by_scope(query, current_user, self.db, Opportunity, "owner_id")
        if sales_id:
            query = query.filter(Opportunity.owner_id == sales_id)
        return query.all()

    def _build_stage_counts(self, opportunities: Iterable[Opportunity]) -> Dict[OpportunityStageEnum, int]:
        stage_counts = {stage: 0 for stage in self.FUNNEL_STAGES}
        stage_index = {stage: index for index, stage in enumerate(self.FUNNEL_STAGES)}

        for opportunity in opportunities:
            opportunity_stage = self._normalize_stage(opportunity.stage)
            if opportunity_stage is None or opportunity_stage == OpportunityStageEnum.LOST:
                continue

            current_index = stage_index[opportunity_stage]
            for stage in self.FUNNEL_STAGES:
                if stage == OpportunityStageEnum.WON:
                    if opportunity_stage == OpportunityStageEnum.WON:
                        stage_counts[stage] += 1
                elif current_index >= stage_index[stage]:
                    stage_counts[stage] += 1

        return stage_counts

    def _calculate_avg_days_in_stage(
        self,
        stage: OpportunityStageEnum,
        start_dt: date,
        end_dt: date,
        sales_id: Optional[int],
        current_user: Optional[User],
    ) -> Optional[float]:
        if stage not in self.ACTIVE_PIPELINE_STAGES:
            return None

        stage_exit_days = self._get_stage_exit_days(
            stage=stage,
            start_dt=start_dt,
            end_dt=end_dt,
            sales_id=sales_id,
            current_user=current_user,
        )
        current_stage_days = self._get_current_stage_days(
            stage=stage,
            start_dt=start_dt,
            end_dt=end_dt,
            sales_id=sales_id,
            current_user=current_user,
        )
        samples = stage_exit_days + current_stage_days
        if not samples:
            return None
        return round(sum(samples) / len(samples), 1)

    def _get_stage_exit_days(
        self,
        stage: OpportunityStageEnum,
        start_dt: date,
        end_dt: date,
        sales_id: Optional[int],
        current_user: Optional[User],
    ) -> List[float]:
        start_at = datetime.combine(start_dt, time.min)
        end_exclusive = datetime.combine(end_dt + timedelta(days=1), time.min)
        query = (
            self.db.query(FunnelTransitionLog)
            .join(Opportunity, Opportunity.id == FunnelTransitionLog.entity_id)
            .filter(
                FunnelTransitionLog.entity_type == "OPPORTUNITY",
                FunnelTransitionLog.from_stage == stage.value,
                FunnelTransitionLog.transitioned_at >= start_at,
                FunnelTransitionLog.transitioned_at < end_exclusive,
                FunnelTransitionLog.dwell_hours.isnot(None),
            )
        )
        if current_user is not None:
            query = filter_sales_data_by_scope(query, current_user, self.db, Opportunity, "owner_id")
        if sales_id:
            query = query.filter(Opportunity.owner_id == sales_id)

        return [
            round(float(log.dwell_hours or 0) / 24, 1)
            for log in query.all()
            if float(log.dwell_hours or 0) > 0
        ]

    def _get_current_stage_days(
        self,
        stage: OpportunityStageEnum,
        start_dt: date,
        end_dt: date,
        sales_id: Optional[int],
        current_user: Optional[User],
    ) -> List[float]:
        start_at = datetime.combine(start_dt, time.min)
        end_exclusive = datetime.combine(end_dt + timedelta(days=1), time.min)
        cutoff_dt = min(datetime.now(), datetime.combine(end_dt, time.max))

        query = self.db.query(Opportunity).filter(
            Opportunity.stage == stage.value,
            Opportunity.created_at < end_exclusive,
        )
        if current_user is not None:
            query = filter_sales_data_by_scope(query, current_user, self.db, Opportunity, "owner_id")
        if sales_id:
            query = query.filter(Opportunity.owner_id == sales_id)

        opportunities = query.all()
        if not opportunities:
            return []

        stage_entry_map = self._get_stage_entry_times(
            stage=stage,
            opportunity_ids=[opp.id for opp in opportunities],
            cutoff_dt=cutoff_dt,
        )
        current_days = []
        for opportunity in opportunities:
            entered_at = stage_entry_map.get(opportunity.id) or opportunity.created_at
            if entered_at is None or entered_at > cutoff_dt or entered_at < start_at:
                continue

            dwell_days = round((cutoff_dt - entered_at).total_seconds() / 86400, 1)
            if dwell_days >= 0:
                current_days.append(dwell_days)

        return current_days

    def _get_stage_entry_times(
        self,
        stage: OpportunityStageEnum,
        opportunity_ids: List[int],
        cutoff_dt: datetime,
    ) -> Dict[int, datetime]:
        if not opportunity_ids:
            return {}

        rows = (
            self.db.query(FunnelTransitionLog)
            .filter(
                FunnelTransitionLog.entity_type == "OPPORTUNITY",
                FunnelTransitionLog.to_stage == stage.value,
                FunnelTransitionLog.entity_id.in_(opportunity_ids),
                FunnelTransitionLog.transitioned_at <= cutoff_dt,
            )
            .order_by(
                FunnelTransitionLog.entity_id.asc(),
                FunnelTransitionLog.transitioned_at.desc(),
            )
            .all()
        )

        entry_times: Dict[int, datetime] = {}
        for row in rows:
            if row.entity_id not in entry_times:
                entry_times[row.entity_id] = row.transitioned_at
        return entry_times

    def _calculate_pipeline_metrics(self, opportunities: Iterable[Opportunity]) -> Dict[str, float]:
        total_pipeline = 0.0
        weighted_pipeline = 0.0
        pipeline_count = 0

        for opportunity in opportunities:
            stage = self._normalize_stage(opportunity.stage)
            if stage is None or stage in (OpportunityStageEnum.WON, OpportunityStageEnum.LOST):
                continue

            amount = float(opportunity.est_amount or 0)
            probability = (
                float(opportunity.probability)
                if opportunity.probability is not None
                else self.DEFAULT_STAGE_PROBABILITIES.get(stage, 0.0)
            )
            total_pipeline += amount
            weighted_pipeline += amount * probability / 100
            pipeline_count += 1

        return {
            "total_pipeline_value": round(total_pipeline, 2),
            "weighted_pipeline_value": round(weighted_pipeline, 2),
            "pipeline_opportunity_count": pipeline_count,
        }

    def _calculate_avg_sales_cycle_days(self, won_opportunities: Iterable[Opportunity]) -> float:
        durations = []
        for opportunity in won_opportunities:
            if opportunity.updated_at and opportunity.created_at:
                durations.append((opportunity.updated_at.date() - opportunity.created_at.date()).days)
        if not durations:
            return 0.0
        return round(sum(durations) / len(durations), 1)

    def _resolve_stage_trend(
        self,
        current_stage_metrics: Dict[str, Any],
        previous_stage_metrics: Dict[str, Any],
    ) -> str:
        current_rate = current_stage_metrics.get("conversion_to_next")
        previous_rate = previous_stage_metrics.get("conversion_to_next")
        if current_rate is not None and previous_rate is not None:
            diff = current_rate - previous_rate
            if diff >= 3:
                return "up"
            if diff <= -3:
                return "down"
            return "stable"

        current_days = current_stage_metrics.get("avg_days_in_stage")
        previous_days = previous_stage_metrics.get("avg_days_in_stage")
        if current_days is not None and previous_days is not None:
            diff = current_days - previous_days
            if diff <= -2:
                return "up"
            if diff >= 2:
                return "down"

        return "stable"

    def _build_bottleneck_payload(
        self,
        conversion_data: Dict[str, Any],
        threshold: float,
        analysis_date: date,
    ) -> Dict[str, Any]:
        bottlenecks = []

        for stage_data in conversion_data.get("stages", []):
            stage_value = stage_data["stage"]
            stage_enum = self._normalize_stage(stage_value)
            conversion_rate = stage_data.get("conversion_to_next")
            avg_days = stage_data.get("avg_days_in_stage")
            benchmark_rate = BENCHMARK_CONVERSION_RATES.get(stage_enum, 60.0)
            benchmark_days = BENCHMARK_DAYS_IN_STAGE.get(stage_enum, 14.0)

            if conversion_rate is not None and conversion_rate < threshold:
                gap = round(conversion_rate - benchmark_rate, 1)
                severity = "HIGH" if gap < -10 else "MEDIUM"
                lost_opps = max(1, int((benchmark_rate - conversion_rate) / 10))
                impact = (
                    f"每月约损失 {lost_opps}-{lost_opps + 2} 个商机，"
                    f"预计金额 {lost_opps * 200}-{(lost_opps + 2) * 300} 万"
                )
                bottlenecks.append(
                    {
                        "stage": stage_value,
                        "stage_name": stage_data["stage_name"],
                        "issue_type": "low_conversion",
                        "current_rate": conversion_rate,
                        "benchmark_rate": benchmark_rate,
                        "gap": gap,
                        "severity": severity,
                        "impact": impact,
                        "root_causes": self.ROOT_CAUSES_BY_STAGE.get(stage_value, ["需进一步分析"])[:3],
                        "recommendations": self.RECOMMENDATIONS_BY_STAGE.get(stage_value, ["需进一步分析"])[:4],
                    }
                )

            if avg_days is not None and benchmark_days and avg_days > benchmark_days * 1.3:
                gap_days = round(avg_days - benchmark_days, 1)
                severity = "HIGH" if gap_days > benchmark_days * 0.5 else "MEDIUM"
                bottlenecks.append(
                    {
                        "stage": stage_value,
                        "stage_name": stage_data["stage_name"],
                        "issue_type": "long_stay",
                        "current_days": avg_days,
                        "benchmark_days": benchmark_days,
                        "gap": gap_days,
                        "severity": severity,
                        "impact": f"销售周期延长约 {int(gap_days)} 天，影响整体效率",
                        "root_causes": self.ROOT_CAUSES_BY_STAGE.get(stage_value, ["需进一步分析"])[:2],
                        "recommendations": self.RECOMMENDATIONS_BY_STAGE.get(stage_value, ["需进一步分析"])[:3],
                    }
                )

        high_count = len([item for item in bottlenecks if item["severity"] == "HIGH"])
        medium_count = len([item for item in bottlenecks if item["severity"] == "MEDIUM"])
        health_score = max(0, 100 - high_count * 15 - medium_count * 8)

        return {
            "analysis_date": analysis_date.isoformat(),
            "threshold": threshold,
            "bottlenecks_found": len(bottlenecks),
            "high_severity": high_count,
            "medium_severity": medium_count,
            "bottlenecks": bottlenecks,
            "overall_health_score": health_score,
        }

    def _get_closed_opportunities(
        self,
        start_dt: date,
        end_dt: date,
        current_user: Optional[User],
    ) -> List[Opportunity]:
        start_at = datetime.combine(start_dt, time.min)
        end_exclusive = datetime.combine(end_dt + timedelta(days=1), time.min)
        query = self.db.query(Opportunity).filter(
            Opportunity.updated_at >= start_at,
            Opportunity.updated_at < end_exclusive,
            Opportunity.stage.in_([OpportunityStageEnum.WON.value, OpportunityStageEnum.LOST.value]),
        )
        if current_user is not None:
            query = filter_sales_data_by_scope(query, current_user, self.db, Opportunity, "owner_id")
        return query.all()

    def _build_prediction_accuracy_by_stage(
        self,
        closed_opps: List[Opportunity],
        overall_actual_win_rate: float,
    ) -> List[Dict[str, Any]]:
        grouped_opportunities: Dict[OpportunityStageEnum, Dict[str, Any]] = {
            stage: {"opportunities": [], "source_counts": {}}
            for stage in self.ACTIVE_PIPELINE_STAGES
        }
        stage_map = self._get_last_active_stage_map(closed_opps)

        for opportunity in closed_opps:
            stage_info = stage_map.get(opportunity.id)
            if stage_info is None:
                inferred_stage = self._infer_stage_from_probability(opportunity.probability)
                if inferred_stage is None:
                    continue
                stage_info = (inferred_stage, "probability_inferred")

            stage, source = stage_info
            bucket = grouped_opportunities.get(stage)
            if bucket is None:
                continue
            bucket["opportunities"].append(opportunity)
            bucket["source_counts"][source] = bucket["source_counts"].get(source, 0) + 1

        stage_analysis = []
        for index, stage in enumerate(self.ACTIVE_PIPELINE_STAGES, start=1):
            bucket = grouped_opportunities[stage]
            opportunities = bucket["opportunities"]
            if opportunities:
                stage_predicted = round(
                    sum(self._get_opportunity_prediction_probability(opportunity, stage) for opportunity in opportunities)
                    / len(opportunities),
                    1,
                )
                stage_won = len(
                    [opportunity for opportunity in opportunities if opportunity.stage == OpportunityStageEnum.WON.value]
                )
                stage_actual = round(stage_won / len(opportunities) * 100, 1)
                stage_accuracy = round(100 - abs(stage_predicted - stage_actual), 1)
                stage_diff = stage_predicted - stage_actual
                stage_bias = self._resolve_accuracy_bias(stage_diff)
            else:
                stage_predicted = self._get_stage_baseline_probability(stage)
                stage_actual = overall_actual_win_rate
                stage_accuracy = None
                stage_bias = "数据不足"
                stage_won = 0

            stage_analysis.append(
                {
                    "stage": stage.value,
                    "stage_name": STAGE_DISPLAY_NAMES.get(stage, stage.value),
                    "stage_order": index,
                    "predicted": stage_predicted,
                    "actual": stage_actual,
                    "accuracy": max(0, min(100, stage_accuracy)) if stage_accuracy is not None else None,
                    "bias": stage_bias,
                    "sample_size": len(opportunities),
                    "won_count": stage_won,
                    "data_source": self._resolve_stage_analysis_source(bucket["source_counts"]),
                }
            )

        return stage_analysis

    def _get_last_active_stage_map(
        self,
        closed_opps: List[Opportunity],
    ) -> Dict[int, tuple[OpportunityStageEnum, str]]:
        opportunity_ids = [opportunity.id for opportunity in closed_opps]
        if not opportunity_ids:
            return {}

        rows = (
            self.db.query(FunnelTransitionLog)
            .filter(
                FunnelTransitionLog.entity_type == "OPPORTUNITY",
                FunnelTransitionLog.entity_id.in_(opportunity_ids),
            )
            .order_by(
                FunnelTransitionLog.entity_id.asc(),
                FunnelTransitionLog.transitioned_at.desc(),
            )
            .all()
        )

        grouped_logs: Dict[int, List[FunnelTransitionLog]] = {}
        for row in rows:
            grouped_logs.setdefault(row.entity_id, []).append(row)

        result: Dict[int, tuple[OpportunityStageEnum, str]] = {}
        for opportunity in closed_opps:
            logs = grouped_logs.get(opportunity.id, [])
            terminal_log = next(
                (
                    row
                    for row in logs
                    if self._normalize_stage(row.to_stage) in (OpportunityStageEnum.WON, OpportunityStageEnum.LOST)
                    and self._normalize_stage(row.from_stage) in self.ACTIVE_PIPELINE_STAGES
                ),
                None,
            )
            if terminal_log:
                stage = self._normalize_stage(terminal_log.from_stage)
                if stage is not None:
                    result[opportunity.id] = (stage, "terminal_transition")
                    continue

            active_to_log = next(
                (
                    row
                    for row in logs
                    if self._normalize_stage(row.to_stage) in self.ACTIVE_PIPELINE_STAGES
                ),
                None,
            )
            if active_to_log:
                stage = self._normalize_stage(active_to_log.to_stage)
                if stage is not None:
                    result[opportunity.id] = (stage, "active_transition")
                    continue

            active_from_log = next(
                (
                    row
                    for row in logs
                    if self._normalize_stage(row.from_stage) in self.ACTIVE_PIPELINE_STAGES
                ),
                None,
            )
            if active_from_log:
                stage = self._normalize_stage(active_from_log.from_stage)
                if stage is not None:
                    result[opportunity.id] = (stage, "active_transition")

        return result

    def _get_opportunity_prediction_probability(
        self,
        opportunity: Opportunity,
        stage: OpportunityStageEnum,
    ) -> float:
        if opportunity.probability is not None:
            return float(opportunity.probability)
        return self._get_stage_baseline_probability(stage)

    def _get_stage_baseline_probability(self, stage: OpportunityStageEnum) -> float:
        if stage in self.forecast_service.STAGE_WIN_RATES:
            return round(self.forecast_service.STAGE_WIN_RATES[stage] * 100, 1)
        return round(float(self.DEFAULT_STAGE_PROBABILITIES.get(stage, 0.0)), 1)

    def _resolve_stage_analysis_source(self, source_counts: Dict[str, int]) -> str:
        if not source_counts:
            return "insufficient_data"
        primary_source, _ = max(source_counts.items(), key=lambda item: item[1])
        return primary_source

    def _resolve_accuracy_bias(self, diff: float) -> str:
        if abs(diff) < 5:
            return "准确"
        if diff > 0:
            return "乐观"
        return "保守"

    def _infer_stage_from_probability(
        self,
        probability: Optional[int],
    ) -> Optional[OpportunityStageEnum]:
        value = float(probability or 0)
        if value >= 85:
            return OpportunityStageEnum.CLOSING
        if value >= 70:
            return OpportunityStageEnum.NEGOTIATION
        if value >= 50:
            return OpportunityStageEnum.PROPOSAL
        if value >= 30:
            return OpportunityStageEnum.QUALIFICATION
        if value > 0:
            return OpportunityStageEnum.DISCOVERY
        return None

    def _get_previous_period(self, start_dt: date, end_dt: date) -> tuple[date, date]:
        days = (end_dt - start_dt).days + 1
        previous_end = start_dt - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)
        return previous_start, previous_end

    def _iter_recent_months(self, months: int, end_dt: date) -> Iterable[tuple[int, int]]:
        end_index = end_dt.year * 12 + end_dt.month - 1
        start_index = end_index - months + 1
        for index in range(start_index, end_index + 1):
            year = index // 12
            month = index % 12 + 1
            yield year, month

    def _resolve_score_trend(self, current_score: float, previous_score: float) -> str:
        diff = current_score - previous_score
        if diff >= 5:
            return "up"
        if diff <= -5:
            return "down"
        return "stable"

    @staticmethod
    def _normalize_stage(stage_value: Optional[str]) -> Optional[OpportunityStageEnum]:
        if not stage_value:
            return None
        try:
            return OpportunityStageEnum(stage_value)
        except ValueError:
            return None
