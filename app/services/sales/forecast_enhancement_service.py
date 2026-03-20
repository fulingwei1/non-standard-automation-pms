# -*- coding: utf-8 -*-
"""
销售预测增强分析服务

将增强版预测接口中的静态演示数据替换为基于真实业务表的动态统计。
"""

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from statistics import mean
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.common.date_range import get_last_month_range, get_month_range, get_month_range_by_ym
from app.models.enums.sales import OpportunityStageEnum
from app.models.sales import (
    Contract,
    Lead,
    LeadFollowUp,
    Opportunity,
    Quote,
    SalesTarget,
    SalesTeam,
    SalesTeamMember,
)
from app.models.user import User
from app.services.sales.target_performance_service import SalesTargetPerformanceService
from app.services.sales_forecast_service import SalesForecastService


@dataclass
class PeriodContext:
    period: str
    label: str
    start_date: date
    end_date: date
    start_dt: datetime
    end_exclusive: datetime
    scale: int


class SalesForecastEnhancementService:
    """销售预测增强分析服务。"""

    ACTIVE_OPPORTUNITY_STAGES = (
        OpportunityStageEnum.DISCOVERY.value,
        OpportunityStageEnum.QUALIFICATION.value,
        OpportunityStageEnum.PROPOSAL.value,
        OpportunityStageEnum.NEGOTIATION.value,
        OpportunityStageEnum.CLOSING.value,
    )
    CLOSED_OPPORTUNITY_STAGES = (
        OpportunityStageEnum.WON.value,
        OpportunityStageEnum.LOST.value,
    )
    FOLLOW_UP_ALERT_DAYS = 7
    FOLLOW_UP_RISK_DAYS = 14
    QUALITY_WEIGHTS = {
        "lead_completeness": 20,
        "follow_up_timeliness": 25,
        "decision_chain": 25,
        "visit_records": 15,
        "close_reason": 15,
    }

    def __init__(self, db: Session):
        self.db = db
        self.forecast_service = SalesForecastService(db)
        self.target_performance_service = SalesTargetPerformanceService(db)

    def get_enhanced_prediction(self, period: str = "quarterly") -> Dict[str, Any]:
        """获取增强版销售预测。"""
        period_context = self._get_period_context(period)
        forecast = self.forecast_service.get_company_forecast(period=period)
        quality = self._build_company_quality_factor()
        activity = self._build_company_activity_factor(period_context)
        health = self._build_company_health_factor()
        historical_accuracy = self._build_historical_accuracy_factor()
        seasonality = self._build_seasonality_factor(period_context)

        base_predicted = float(forecast["prediction"]["predicted_revenue"])
        target_value = float(forecast["targets"]["quarterly_target"])

        adjustments = {
            "data_quality": round(base_predicted * quality["impact"], 2),
            "activity": round(base_predicted * activity["impact"], 2),
            "health": round(base_predicted * health["impact"], 2),
            "seasonality": round(base_predicted * seasonality["impact"], 2),
        }
        total_adjustment = round(sum(adjustments.values()), 2)
        final_predicted = round(max(0.0, base_predicted + total_adjustment), 2)
        final_completion_rate = round(
            (final_predicted / target_value * 100) if target_value > 0 else 0.0,
            2,
        )
        confidence_level = max(
            50,
            min(
                100,
                int(
                    round(
                        (
                            float(forecast["prediction"]["confidence_level"])
                            + quality["overall_score"]
                            + health["overall_score"]
                        )
                        / 3
                    )
                ),
            ),
        )

        return {
            "period": forecast["period"],
            "period_type": forecast["period_type"],
            "generated_at": forecast["generated_at"],
            "target_source": forecast["target_source"],
            "base_prediction": {
                "formula": "已完成 + Σ(漏斗金额 × 阶段赢单率)",
                "completed": round(float(forecast["targets"]["actual_revenue"]), 2),
                "pipeline_weighted": round(
                    float(forecast["funnel_contribution"].get("total_weighted", 0.0)),
                    2,
                ),
                "base_predicted": round(base_predicted, 2),
                "base_completion_rate": round(
                    float(forecast["prediction"]["predicted_completion_rate"]),
                    2,
                ),
            },
            "data_quality_factor": quality,
            "activity_factor": activity,
            "opportunity_health_factor": health,
            "historical_accuracy_factor": historical_accuracy,
            "seasonality_factor": seasonality,
            "final_prediction": {
                "base": round(base_predicted, 2),
                "adjustments": adjustments,
                "total_adjustment": total_adjustment,
                "final_predicted": final_predicted,
                "final_completion_rate": final_completion_rate,
                "confidence_level": confidence_level,
                "confidence_interval": forecast["prediction"]["confidence_interval"],
            },
            "key_insights": self._build_key_insights(
                base_predicted=base_predicted,
                quality=quality,
                activity=activity,
                health=health,
            ),
            "improvement_recommendations": self._build_recommendations(
                quality=quality,
                health=health,
                activity=activity,
            ),
        }

    def get_data_quality_score(self, sales_id: Optional[int] = None) -> Dict[str, Any]:
        """获取销售数据质量评分。"""
        profiles = self._get_quality_profiles(sales_id=sales_id)
        rankings = []
        for index, profile in enumerate(profiles, start=1):
            rankings.append(
                {
                    "rank": index,
                    "sales_id": profile["sales_id"],
                    "sales_name": profile["sales_name"],
                    "team": profile["team"],
                    "overall_score": profile["overall_score"],
                    "dimensions": profile["dimensions_map"],
                    "opportunities_count": profile["opportunities_count"],
                    "healthy_opportunities": profile["healthy_opportunities"],
                    "prediction_accuracy": profile["prediction_accuracy"],
                    "prediction_accuracy_source": profile["prediction_accuracy_source"],
                    "alerts": profile["alerts"],
                }
            )

        company_average = round(mean([item["overall_score"] for item in profiles]), 1) if profiles else 0.0
        top_performer = profiles[0] if profiles else None
        needs_improvement = profiles[-1] if profiles else None

        return {
            "assessment_date": date.today().isoformat(),
            "team_average": company_average,
            "company_average": company_average,
            "top_performer": (
                {"name": top_performer["sales_name"], "score": top_performer["overall_score"]}
                if top_performer
                else None
            ),
            "needs_improvement": (
                {
                    "name": needs_improvement["sales_name"],
                    "score": needs_improvement["overall_score"],
                }
                if needs_improvement
                else None
            ),
            "rankings": rankings,
            "scoring_rules": {
                "lead_completeness": {
                    "name": "线索完整度",
                    "weight": 20,
                    "criteria": "预算、金额、风险和预计成交时间等关键信息填写完整",
                },
                "follow_up_timeliness": {
                    "name": "跟进及时性",
                    "weight": 25,
                    "criteria": "活跃商机 7 天内存在最新跟进记录",
                },
                "decision_chain": {
                    "name": "决策链完整度",
                    "weight": 25,
                    "criteria": "活跃商机补全决策链字段",
                },
                "visit_records": {
                    "name": "拜访记录完整度",
                    "weight": 15,
                    "criteria": "近 30 天商机/线索至少存在拜访或会议类跟进",
                },
                "close_reason": {
                    "name": "关闭信息完整度",
                    "weight": 15,
                    "criteria": "赢单/输单商机保留关键跟进痕迹和决策信息",
                },
            },
            "impact_explanation": {
                "on_prediction": "当前使用真实 CRM 字段完整度和跟进时效，动态修正预测可信度",
                "on_performance": "低分销售可优先进入数据补录、商机复盘和销售辅导名单",
                "on_support": "分数和预警项会帮助管理层定位需要支持的销售人员",
            },
        }

    def get_activity_tracking(
        self,
        sales_id: Optional[int] = None,
        period: str = "monthly",
    ) -> Dict[str, Any]:
        """获取销售动作追踪。"""
        period_context = self._get_period_context(period)
        user_ids = self._get_sales_user_ids(sales_id=sales_id)
        profiles = [
            self._build_activity_profile(user_id, period_context)
            for user_id in user_ids
        ]
        profiles = [profile for profile in profiles if profile is not None]

        team_summary = self._aggregate_activity_summary(profiles)
        high_activity_win_rates = [
            item["correlation"]["high_activity_win_rate"]
            for item in profiles
            if item["correlation"]["high_activity_opps"] > 0
        ]
        low_activity_win_rates = [
            item["correlation"]["low_activity_win_rate"]
            for item in profiles
            if item["correlation"]["low_activity_opps"] > 0
        ]
        high_activity_avg = round(mean(high_activity_win_rates), 1) if high_activity_win_rates else 0.0
        low_activity_avg = round(mean(low_activity_win_rates), 1) if low_activity_win_rates else 0.0
        response_hours = [
            item["avg_response_time_hours"]
            for item in profiles
            if item["avg_response_time_hours"] is not None
        ]
        avg_response_hours = round(mean(response_hours), 1) if response_hours else 0.0

        return {
            "period": period_context.label,
            "team_summary": team_summary,
            "individual_tracking": profiles,
            "insights": self._build_activity_insights(
                high_activity_avg=high_activity_avg,
                low_activity_avg=low_activity_avg,
                avg_response_hours=avg_response_hours,
            ),
        }

    def get_accuracy_comparison(self) -> Dict[str, Any]:
        """对比不同数据质量层级下的经营兑现情况。"""
        profiles = self._get_quality_profiles()
        band_profiles = {
            "high_data_quality": [
                profile for profile in profiles if profile["overall_score"] >= 90
            ],
            "medium_data_quality": [
                profile for profile in profiles if 70 <= profile["overall_score"] < 90
            ],
            "low_data_quality": [
                profile for profile in profiles if profile["overall_score"] < 70
            ],
        }

        result = {
            "high_data_quality": self._build_accuracy_band(
                "数据质量>=90 分的销售",
                band_profiles["high_data_quality"],
                ["决策链信息较完整", "跟进频率稳定", "拜访/会议记录覆盖较好"],
            ),
            "medium_data_quality": self._build_accuracy_band(
                "数据质量 70-90 分的销售",
                band_profiles["medium_data_quality"],
                ["关键字段大多齐全", "部分商机存在跟进时效压力", "执行节奏基本稳定"],
            ),
            "low_data_quality": self._build_accuracy_band(
                "数据质量<70 分的销售",
                band_profiles["low_data_quality"],
                ["关键信息缺失较多", "跟进经常滞后", "需要重点补录和复盘"],
            ),
        }

        high_band = result["high_data_quality"]
        low_band = result["low_data_quality"]
        key_findings = []
        if high_band["sales_count"] and low_band["sales_count"]:
            accuracy_gap = round(
                high_band["avg_prediction_accuracy"] - low_band["avg_prediction_accuracy"],
                1,
            )
            win_rate_gap = round(high_band["avg_win_rate"] - low_band["avg_win_rate"], 1)
            cycle_gap = round(low_band["avg_sales_cycle_days"] - high_band["avg_sales_cycle_days"], 1)
            key_findings = [
                f"高数据质量销售的经营兑现度高出 {accuracy_gap} 分",
                f"高数据质量销售的赢单率高出 {win_rate_gap} 个百分点",
                f"高数据质量销售的成交周期平均缩短 {cycle_gap} 天",
            ]
        else:
            key_findings = ["当前数据量不足以形成完整分层对比，结果会随着业务数据积累自动更新"]

        return {
            **result,
            "key_findings": key_findings,
            "conclusion": "当前对比已基于真实销售、跟进、合同和目标数据生成，不再返回固定演示值",
        }

    def _get_period_context(self, period: str) -> PeriodContext:
        normalized_period = (period or "monthly").lower()
        today = date.today()

        if normalized_period == "yearly":
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
            label = str(today.year)
            scale = 12
        elif normalized_period == "quarterly":
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date, _ = get_month_range_by_ym(today.year, start_month)
            _, end_date = get_month_range_by_ym(today.year, start_month + 2)
            label = f"{today.year}-Q{quarter}"
            scale = 3
        else:
            start_date, end_date = get_month_range(today)
            label = f"{today.year}-{today.month:02d}"
            scale = 1

        return PeriodContext(
            period=normalized_period,
            label=label,
            start_date=start_date,
            end_date=end_date,
            start_dt=datetime.combine(start_date, time.min),
            end_exclusive=datetime.combine(end_date + timedelta(days=1), time.min),
            scale=scale,
        )

    def _get_sales_user_ids(self, sales_id: Optional[int] = None) -> List[int]:
        if sales_id is not None:
            user = self.db.query(User).filter(User.id == sales_id, User.is_active.is_(True)).first()
            return [user.id] if user else []

        user_ids = set()
        for rows in (
            self.db.query(Lead.owner_id).filter(Lead.owner_id.isnot(None)).distinct().all(),
            self.db.query(Opportunity.owner_id)
            .filter(Opportunity.owner_id.isnot(None))
            .distinct()
            .all(),
            self.db.query(Contract.sales_owner_id)
            .filter(Contract.sales_owner_id.isnot(None))
            .distinct()
            .all(),
            self.db.query(Quote.owner_id).filter(Quote.owner_id.isnot(None)).distinct().all(),
        ):
            user_ids.update(row[0] for row in rows if row[0] is not None)

        if not user_ids:
            return []

        return [
            user_id
            for user_id, in self.db.query(User.id)
            .filter(User.id.in_(sorted(user_ids)), User.is_active.is_(True))
            .order_by(User.id.asc())
            .all()
        ]

    def _get_display_name(self, user: Optional[User]) -> str:
        if not user:
            return "未知销售"
        return user.real_name or user.username or f"用户{user.id}"

    def _get_user_team_name(self, user: Optional[User]) -> str:
        if not user:
            return "未分配团队"

        membership = (
            self.db.query(SalesTeamMember, SalesTeam)
            .join(SalesTeam, SalesTeam.id == SalesTeamMember.team_id)
            .filter(
                SalesTeamMember.user_id == user.id,
                SalesTeamMember.is_active.is_(True),
                SalesTeam.is_active.is_(True),
            )
            .order_by(SalesTeamMember.is_primary.desc(), SalesTeamMember.id.asc())
            .first()
        )
        if membership:
            _, team = membership
            return team.team_name
        return user.department or "未分配团队"

    def _get_recent_follow_up_map(self, lead_ids: List[int]) -> Dict[int, datetime]:
        if not lead_ids:
            return {}

        rows = (
            self.db.query(
                LeadFollowUp.lead_id,
                func.max(LeadFollowUp.created_at).label("last_follow_up_at"),
            )
            .filter(LeadFollowUp.lead_id.in_(lead_ids))
            .group_by(LeadFollowUp.lead_id)
            .all()
        )
        return {lead_id: last_follow_up_at for lead_id, last_follow_up_at in rows if last_follow_up_at}

    def _get_recent_visit_leads(self, lead_ids: List[int]) -> set[int]:
        if not lead_ids:
            return set()

        threshold = datetime.now() - timedelta(days=30)
        rows = (
            self.db.query(LeadFollowUp.lead_id)
            .filter(
                LeadFollowUp.lead_id.in_(lead_ids),
                LeadFollowUp.follow_up_type.in_(["VISIT", "MEETING"]),
                LeadFollowUp.created_at >= threshold,
            )
            .distinct()
            .all()
        )
        return {lead_id for lead_id, in rows}

    def _evaluate_health(self, opportunities: List[Opportunity]) -> Dict[str, Any]:
        active_opportunities = [
            opportunity
            for opportunity in opportunities
            if opportunity.stage in self.ACTIVE_OPPORTUNITY_STAGES
        ]
        lead_ids = sorted({opportunity.lead_id for opportunity in active_opportunities if opportunity.lead_id})
        last_follow_up_map = self._get_recent_follow_up_map(lead_ids)
        healthy_count = 0
        healthy_amount = 0.0
        risk_details = []
        risk_amount = 0.0

        for opportunity in active_opportunities:
            reasons = []
            last_follow_up_at = last_follow_up_map.get(opportunity.lead_id)
            if last_follow_up_at is None or (
                datetime.now() - last_follow_up_at
            ).days >= self.FOLLOW_UP_RISK_DAYS:
                reasons.append("超过14天未跟进")

            if not (opportunity.decision_chain or "").strip():
                reasons.append("决策链缺失")

            if opportunity.expected_close_date is None:
                reasons.append("预计成交日期缺失")
            elif opportunity.expected_close_date < date.today():
                reasons.append("预计成交已逾期")

            amount = float(opportunity.est_amount or 0)
            if reasons:
                risk_amount += amount
                risk_details.append(
                    {
                        "name": opportunity.opp_name,
                        "amount": round(amount, 2),
                        "risk": reasons[0],
                    }
                )
            else:
                healthy_count += 1
                healthy_amount += amount

        total_active = len(active_opportunities)
        healthy_rate = healthy_count / total_active if total_active else 1.0
        overall_score = round(max(0.0, min(100.0, healthy_rate * 100)), 1)
        impact = round(-min(0.08, (1 - healthy_rate) * 0.08), 4)

        return {
            "overall_score": overall_score,
            "impact": impact,
            "healthy_opportunities": {
                "count": healthy_count,
                "total_amount": round(healthy_amount, 2),
                "criteria": "7天内有跟进 + 决策链完整 + 预计成交日期明确",
            },
            "at_risk_opportunities": {
                "count": len(risk_details),
                "total_amount": round(risk_amount, 2),
                "criteria": "超过14天未跟进、决策链缺失或预计成交已逾期",
                "details": sorted(risk_details, key=lambda item: item["amount"], reverse=True)[:3],
            },
        }

    def _build_quality_profile(self, user_id: int) -> Dict[str, Any]:
        user = self.db.query(User).filter(User.id == user_id).first()
        opportunities = self.db.query(Opportunity).filter(Opportunity.owner_id == user_id).all()
        active_opportunities = [
            opportunity
            for opportunity in opportunities
            if opportunity.stage in self.ACTIVE_OPPORTUNITY_STAGES
        ]
        closed_opportunities = [
            opportunity
            for opportunity in opportunities
            if opportunity.stage in self.CLOSED_OPPORTUNITY_STAGES
        ]
        relevant_lead_ids = sorted(
            {
                opportunity.lead_id
                for opportunity in opportunities
                if opportunity.lead_id is not None
            }
        )
        if not relevant_lead_ids:
            relevant_lead_ids = [
                lead_id
                for lead_id, in self.db.query(Lead.id)
                .filter(Lead.owner_id == user_id)
                .order_by(Lead.id.asc())
                .all()
            ]

        last_follow_up_map = self._get_recent_follow_up_map(relevant_lead_ids)
        recent_visit_leads = self._get_recent_visit_leads(relevant_lead_ids)

        completeness_fields = [
            lambda item: item.est_amount is not None,
            lambda item: item.expected_close_date is not None,
            lambda item: bool((item.budget_range or "").strip()),
            lambda item: bool((item.risk_level or "").strip()),
            lambda item: bool((item.delivery_window or "").strip()),
        ]
        if active_opportunities:
            lead_completeness_score = round(
                mean(
                    [
                        sum(1 for checker in completeness_fields if checker(opportunity))
                        / len(completeness_fields)
                        * 100
                        for opportunity in active_opportunities
                    ]
                ),
                1,
            )
        else:
            lead_completeness_score = 100.0

        timely_follow_up_count = 0
        decision_chain_count = 0
        visit_covered_count = 0
        for opportunity in active_opportunities:
            last_follow_up_at = last_follow_up_map.get(opportunity.lead_id)
            if last_follow_up_at is not None and (
                datetime.now() - last_follow_up_at
            ).days < self.FOLLOW_UP_ALERT_DAYS:
                timely_follow_up_count += 1
            if (opportunity.decision_chain or "").strip():
                decision_chain_count += 1
            if opportunity.lead_id in recent_visit_leads:
                visit_covered_count += 1

        denominator = len(active_opportunities) or 1
        follow_up_timeliness_score = round(timely_follow_up_count / denominator * 100, 1)
        decision_chain_score = round(decision_chain_count / denominator * 100, 1)
        visit_records_score = round(visit_covered_count / denominator * 100, 1)

        if closed_opportunities:
            close_reason_score = round(
                mean(
                    [
                        100.0
                        if (
                            opportunity.lead_id in last_follow_up_map
                            and (opportunity.decision_chain or "").strip()
                        )
                        else 0.0
                        for opportunity in closed_opportunities
                    ]
                ),
                1,
            )
        else:
            close_reason_score = 100.0

        dimensions_map = {
            "lead_completeness": lead_completeness_score,
            "follow_up_timeliness": follow_up_timeliness_score,
            "decision_chain": decision_chain_score,
            "visit_records": visit_records_score,
            "close_reason": close_reason_score,
        }
        overall_score = round(
            sum(
                dimensions_map[key] * self.QUALITY_WEIGHTS[key]
                for key in self.QUALITY_WEIGHTS
            )
            / sum(self.QUALITY_WEIGHTS.values()),
            1,
        )
        health = self._evaluate_health(opportunities)
        prediction_accuracy, accuracy_source = self._get_user_prediction_accuracy(
            user_id=user_id,
            quality_score=overall_score,
        )

        alerts = []
        if follow_up_timeliness_score < 70:
            alerts.append("活跃商机跟进时效偏低")
        if decision_chain_score < 70:
            alerts.append("决策链信息缺失较多")
        if visit_records_score < 60:
            alerts.append("拜访/会议类跟进覆盖不足")

        return {
            "sales_id": user_id,
            "sales_name": self._get_display_name(user),
            "team": self._get_user_team_name(user),
            "overall_score": overall_score,
            "dimensions_map": dimensions_map,
            "opportunities_count": len(opportunities),
            "healthy_opportunities": health["healthy_opportunities"]["count"],
            "prediction_accuracy": prediction_accuracy,
            "prediction_accuracy_source": accuracy_source,
            "alerts": alerts,
            "win_rate": self._get_user_win_rate(user_id),
            "sales_cycle_days": self._get_user_sales_cycle_days(user_id),
        }

    def _get_quality_profiles(self, sales_id: Optional[int] = None) -> List[Dict[str, Any]]:
        profiles = [
            self._build_quality_profile(user_id)
            for user_id in self._get_sales_user_ids(sales_id=sales_id)
        ]
        return sorted(profiles, key=lambda item: item["overall_score"], reverse=True)

    def _build_company_quality_factor(self) -> Dict[str, Any]:
        profiles = self._get_quality_profiles()
        if not profiles:
            return {
                "overall_score": 100.0,
                "impact": 0.0,
                "dimensions": [],
                "data_source": "sales_crm",
            }

        averages = {
            key: round(mean(profile["dimensions_map"][key] for profile in profiles), 1)
            for key in self.QUALITY_WEIGHTS
        }
        overall_score = round(mean(profile["overall_score"] for profile in profiles), 1)
        impact = round(max(-0.08, min(0.05, (overall_score - 90) / 240)), 4)

        return {
            "overall_score": overall_score,
            "impact": impact,
            "dimensions": [
                {
                    "name": "线索完整度",
                    "score": averages["lead_completeness"],
                    "weight": 20,
                    "description": "金额、预算、风险、交期等关键字段完整度",
                    "issues": self._build_quality_issue(
                        profiles,
                        "lead_completeness",
                        "存在预算/风险/交期字段缺失的活跃商机",
                    ),
                },
                {
                    "name": "跟进及时性",
                    "score": averages["follow_up_timeliness"],
                    "weight": 25,
                    "description": "活跃商机最近 7 天内跟进覆盖率",
                    "issues": self._build_quality_issue(
                        profiles,
                        "follow_up_timeliness",
                        "部分活跃商机超过 7 天未跟进",
                    ),
                },
                {
                    "name": "决策链完整度",
                    "score": averages["decision_chain"],
                    "weight": 25,
                    "description": "活跃商机决策链字段覆盖率",
                    "issues": self._build_quality_issue(
                        profiles,
                        "decision_chain",
                        "关键商机缺少决策链信息",
                    ),
                },
                {
                    "name": "拜访记录完整度",
                    "score": averages["visit_records"],
                    "weight": 15,
                    "description": "近 30 天拜访/会议类跟进覆盖率",
                    "issues": self._build_quality_issue(
                        profiles,
                        "visit_records",
                        "拜访/会议类跟进痕迹不足",
                    ),
                },
                {
                    "name": "关闭信息完整度",
                    "score": averages["close_reason"],
                    "weight": 15,
                    "description": "赢单/输单商机保留关键跟进和决策信息",
                    "issues": self._build_quality_issue(
                        profiles,
                        "close_reason",
                        "关闭商机缺少关键跟进留痕",
                    ),
                },
            ],
            "data_source": "sales_crm",
        }

    def _build_quality_issue(
        self,
        profiles: List[Dict[str, Any]],
        key: str,
        fallback: str,
    ) -> List[str]:
        low_profiles = [profile for profile in profiles if profile["dimensions_map"][key] < 70]
        if not low_profiles:
            return []
        names = "、".join(profile["sales_name"] for profile in low_profiles[:3])
        return [f"{names} {fallback}"]

    def _build_company_health_factor(self) -> Dict[str, Any]:
        opportunities = self.db.query(Opportunity).all()
        health = self._evaluate_health(opportunities)
        health["data_source"] = "opportunities"
        return health

    def _build_company_activity_factor(self, period_context: PeriodContext) -> Dict[str, Any]:
        profiles = [
            profile
            for profile in (
                self._build_activity_profile(user_id, period_context)
                for user_id in self._get_sales_user_ids()
            )
            if profile is not None
        ]
        summary = self._aggregate_activity_summary(profiles)
        completions = [
            summary["visits"]["completion"],
            summary["calls"]["completion"],
            summary["meetings"]["completion"],
            summary["proposals"]["completion"],
            summary["stage_advances"]["completion"],
        ]
        overall_score = round(mean(min(100.0, value) for value in completions), 1) if completions else 100.0
        impact = round(max(-0.03, min(0.03, (overall_score - 60) / 1000)), 4)

        high_rates = [
            item["correlation"]["high_activity_win_rate"]
            for item in profiles
            if item["correlation"]["high_activity_opps"] > 0
        ]
        low_rates = [
            item["correlation"]["low_activity_win_rate"]
            for item in profiles
            if item["correlation"]["low_activity_opps"] > 0
        ]
        high_avg = round(mean(high_rates), 1) if high_rates else 0.0
        low_avg = round(mean(low_rates), 1) if low_rates else 0.0

        return {
            "overall_score": overall_score,
            "impact": impact,
            "metrics": {
                "visits_target": summary["visits"]["target"],
                "visits_actual": summary["visits"]["actual"],
                "visits_completion": summary["visits"]["completion"],
                "calls_target": summary["calls"]["target"],
                "calls_actual": summary["calls"]["actual"],
                "calls_completion": summary["calls"]["completion"],
                "meetings_target": summary["meetings"]["target"],
                "meetings_actual": summary["meetings"]["actual"],
                "meetings_completion": summary["meetings"]["completion"],
                "proposals_target": summary["proposals"]["target"],
                "proposals_actual": summary["proposals"]["actual"],
                "proposals_completion": summary["proposals"]["completion"],
            },
            "correlation_analysis": {
                "high_activity_win_rate": high_avg,
                "low_activity_win_rate": low_avg,
                "insight": (
                    f"高频跟进商机赢单率比低频高 {round(max(0.0, high_avg - low_avg), 1)} 个百分点"
                    if high_avg or low_avg
                    else "当前样本量不足，暂无法形成稳定的动作-赢单相关性"
                ),
            },
            "target_method": "基于活跃商机数量的过程动作基线",
        }

    def _build_activity_profile(
        self,
        user_id: int,
        period_context: PeriodContext,
    ) -> Optional[Dict[str, Any]]:
        user = self.db.query(User).filter(User.id == user_id).first()
        follow_up_rows = (
            self.db.query(
                LeadFollowUp.follow_up_type,
                func.count(LeadFollowUp.id),
            )
            .join(Lead, Lead.id == LeadFollowUp.lead_id)
            .filter(
                Lead.owner_id == user_id,
                LeadFollowUp.created_at >= period_context.start_dt,
                LeadFollowUp.created_at < period_context.end_exclusive,
            )
            .group_by(LeadFollowUp.follow_up_type)
            .all()
        )
        follow_up_map = {follow_up_type: int(count) for follow_up_type, count in follow_up_rows}
        opportunities = self.db.query(Opportunity).filter(Opportunity.owner_id == user_id).all()
        active_opportunity_count = sum(
            1 for opportunity in opportunities if opportunity.stage in self.ACTIVE_OPPORTUNITY_STAGES
        )

        proposals_actual = (
            self.db.query(func.count(Quote.id))
            .outerjoin(Opportunity, Opportunity.id == Quote.opportunity_id)
            .filter(
                Quote.created_at >= period_context.start_dt,
                Quote.created_at < period_context.end_exclusive,
                or_(
                    Quote.owner_id == user_id,
                    and_(Quote.owner_id.is_(None), Opportunity.owner_id == user_id),
                ),
            )
            .scalar()
            or 0
        )
        stage_advances_actual = (
            self.db.query(func.count(Opportunity.id))
            .filter(
                Opportunity.owner_id == user_id,
                Opportunity.updated_at >= period_context.start_dt,
                Opportunity.updated_at < period_context.end_exclusive,
                Opportunity.stage.in_(
                    [
                        OpportunityStageEnum.PROPOSAL.value,
                        OpportunityStageEnum.NEGOTIATION.value,
                        OpportunityStageEnum.CLOSING.value,
                        OpportunityStageEnum.WON.value,
                    ]
                ),
            )
            .scalar()
            or 0
        )

        visit_target = self._ensure_minimum_target(active_opportunity_count, period_context.scale, 1.0)
        call_target = self._ensure_minimum_target(active_opportunity_count, period_context.scale, 4.0)
        meeting_target = self._ensure_minimum_target(active_opportunity_count, period_context.scale, 1.0)
        proposal_target = self._ensure_minimum_target(active_opportunity_count, period_context.scale, 0.4)
        advance_target = self._ensure_minimum_target(active_opportunity_count, period_context.scale, 0.6)

        metrics = {
            "visits": self._build_activity_metric(visit_target, follow_up_map.get("VISIT", 0)),
            "calls": self._build_activity_metric(call_target, follow_up_map.get("CALL", 0)),
            "meetings": self._build_activity_metric(meeting_target, follow_up_map.get("MEETING", 0)),
            "proposals": self._build_activity_metric(proposal_target, int(proposals_actual)),
            "stage_advances": self._build_activity_metric(advance_target, int(stage_advances_actual)),
        }
        response_hours = self._get_user_response_hours(user_id, period_context)
        correlation = self._build_activity_correlation(
            user_id=user_id,
            period_context=period_context,
        )

        alerts = []
        if metrics["visits"]["completion"] < 80:
            alerts.append(f"拜访完成率仅 {metrics['visits']['completion']}%")
        if response_hours is not None and response_hours > 24:
            alerts.append(f"平均首次响应时间 {response_hours} 小时，已超过 24 小时")
        if metrics["stage_advances"]["completion"] < 80:
            alerts.append(f"阶段推进完成率仅 {metrics['stage_advances']['completion']}%")

        return {
            "sales_id": user_id,
            "sales_name": self._get_display_name(user),
            "activities": metrics,
            "avg_response_time_hours": response_hours,
            "opportunities_advanced": int(stage_advances_actual),
            "correlation": correlation,
            "alerts": alerts,
        }

    def _ensure_minimum_target(self, opportunity_count: int, scale: int, factor: float) -> int:
        baseline = int(math.ceil(max(1, opportunity_count) * factor * scale))
        return max(1, baseline)

    def _build_activity_metric(self, target: int, actual: int) -> Dict[str, float]:
        completion = round((actual / target * 100) if target > 0 else 0.0, 1)
        return {"target": target, "actual": actual, "completion": completion}

    def _aggregate_activity_summary(self, profiles: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        summary = {}
        for key in ["visits", "calls", "meetings", "proposals", "stage_advances"]:
            target = sum(item["activities"][key]["target"] for item in profiles)
            actual = sum(item["activities"][key]["actual"] for item in profiles)
            completion = round((actual / target * 100) if target > 0 else 0.0, 1)
            summary[key] = {"target": target, "actual": actual, "completion": completion}
        return summary

    def _build_activity_correlation(
        self,
        user_id: int,
        period_context: PeriodContext,
    ) -> Dict[str, Any]:
        opportunities = (
            self.db.query(Opportunity)
            .filter(
                Opportunity.owner_id == user_id,
                Opportunity.lead_id.isnot(None),
            )
            .all()
        )
        lead_ids = sorted({opportunity.lead_id for opportunity in opportunities if opportunity.lead_id})
        if not lead_ids:
            return {
                "high_activity_opps": 0,
                "high_activity_win_rate": 0.0,
                "low_activity_opps": 0,
                "low_activity_win_rate": 0.0,
            }

        rows = (
            self.db.query(
                LeadFollowUp.lead_id,
                func.count(LeadFollowUp.id).label("follow_up_count"),
            )
            .filter(
                LeadFollowUp.lead_id.in_(lead_ids),
                LeadFollowUp.created_at >= period_context.start_dt,
                LeadFollowUp.created_at < period_context.end_exclusive,
            )
            .group_by(LeadFollowUp.lead_id)
            .all()
        )
        follow_up_count_map = {lead_id: int(follow_up_count) for lead_id, follow_up_count in rows}
        threshold = max(2, period_context.scale * 2)
        high_activity_opps = [
            opportunity
            for opportunity in opportunities
            if follow_up_count_map.get(opportunity.lead_id, 0) >= threshold
        ]
        low_activity_opps = [
            opportunity
            for opportunity in opportunities
            if follow_up_count_map.get(opportunity.lead_id, 0) < threshold
        ]

        return {
            "high_activity_opps": len(high_activity_opps),
            "high_activity_win_rate": self._calculate_opportunity_win_rate(high_activity_opps),
            "low_activity_opps": len(low_activity_opps),
            "low_activity_win_rate": self._calculate_opportunity_win_rate(low_activity_opps),
        }

    def _calculate_opportunity_win_rate(self, opportunities: List[Opportunity]) -> float:
        if not opportunities:
            return 0.0
        won_count = sum(1 for opportunity in opportunities if opportunity.stage == OpportunityStageEnum.WON.value)
        return round(won_count / len(opportunities) * 100, 1)

    def _get_user_response_hours(
        self,
        user_id: int,
        period_context: PeriodContext,
    ) -> Optional[float]:
        leads = (
            self.db.query(Lead)
            .filter(
                Lead.owner_id == user_id,
                Lead.created_at >= period_context.start_dt,
                Lead.created_at < period_context.end_exclusive,
            )
            .all()
        )
        if not leads:
            return None

        lead_ids = [lead.id for lead in leads]
        first_follow_up_rows = (
            self.db.query(
                LeadFollowUp.lead_id,
                func.min(LeadFollowUp.created_at).label("first_follow_up_at"),
            )
            .filter(LeadFollowUp.lead_id.in_(lead_ids))
            .group_by(LeadFollowUp.lead_id)
            .all()
        )
        first_follow_up_map = {
            lead_id: first_follow_up_at
            for lead_id, first_follow_up_at in first_follow_up_rows
            if first_follow_up_at
        }
        response_hours = []
        for lead in leads:
            first_follow_up_at = first_follow_up_map.get(lead.id)
            if not first_follow_up_at or not lead.created_at:
                continue
            delta_hours = (first_follow_up_at - lead.created_at).total_seconds() / 3600
            response_hours.append(delta_hours)

        return round(mean(response_hours), 1) if response_hours else None

    def _build_activity_insights(
        self,
        high_activity_avg: float,
        low_activity_avg: float,
        avg_response_hours: float,
    ) -> List[Dict[str, str]]:
        insights = []
        if high_activity_avg or low_activity_avg:
            insights.append(
                {
                    "insight": "高频跟进商机的赢单率更高",
                    "data": f"高频赢单率 {high_activity_avg}%，低频赢单率 {low_activity_avg}%",
                    "recommendation": "把高价值商机周跟进频次稳定在 2 次以上",
                }
            )
        insights.append(
            {
                "insight": "首次响应时长越短，越容易维持商机温度",
                "data": f"当前样本的平均首次响应时间为 {avg_response_hours} 小时",
                "recommendation": "把新增线索首次触达控制在 24 小时内",
            }
        )
        return insights

    def _build_historical_accuracy_factor(self) -> Dict[str, Any]:
        samples = []
        reference_date = date.today()

        while len(samples) < 3:
            start_date, end_date = get_last_month_range(reference_date)
            target_value = self.forecast_service._get_sales_target(
                start_date.year,
                start_date.month,
                "monthly",
            )
            if target_value > 0:
                actual_value = self.forecast_service._get_actual_revenue(
                    datetime.combine(start_date, time.min),
                    datetime.combine(end_date, time.min),
                )
                accuracy = self._calculate_attainment_accuracy(target_value, actual_value)
                samples.append(
                    {
                        "period": f"{start_date.year}-{start_date.month:02d}",
                        "predicted": round(target_value, 2),
                        "actual": round(actual_value, 2),
                        "accuracy": accuracy,
                    }
                )
            reference_date = start_date
            if reference_date.year < date.today().year - 3:
                break

        avg_accuracy = round(mean(item["accuracy"] for item in samples), 1) if samples else 0.0
        impact = round(-min(0.03, max(0.0, (85 - avg_accuracy) / 300)), 4) if samples else 0.0

        return {
            "avg_accuracy": avg_accuracy,
            "impact": impact,
            "recent_predictions": samples,
            "method": "基于历史目标兑现度的近似值；后续可接入预测快照后升级为真实预测准确率",
        }

    def _build_seasonality_factor(self, period_context: PeriodContext) -> Dict[str, Any]:
        current_month = date.today().month
        factor = self.forecast_service.SEASONAL_FACTORS.get(current_month, 1.0)
        impact = round((factor - 1.0) * 0.3, 4)

        return {
            "current_month": f"{current_month} 月",
            "factor": round(factor, 2),
            "impact": impact,
            "historical_pattern": "季节性因子来自预测服务配置，会随月份自动切换",
        }

    def _build_key_insights(
        self,
        *,
        base_predicted: float,
        quality: Dict[str, Any],
        activity: Dict[str, Any],
        health: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        insights = []
        data_quality_impact = abs(round(base_predicted * quality["impact"], 2))
        if quality["impact"] < 0:
            insights.append(
                {
                    "type": "WARNING",
                    "title": "数据质量正在拉低预测可信度",
                    "description": f"当前数据质量分 {quality['overall_score']}，对应预测修正 {quality['impact'] * 100:.1f}%",
                    "action": "优先补齐决策链、预算和交期字段，缩短未跟进商机时长",
                    "impact": data_quality_impact,
                }
            )
        if health["at_risk_opportunities"]["count"] > 0:
            insights.append(
                {
                    "type": "WARNING",
                    "title": "存在需要重点盯防的风险商机",
                    "description": (
                        f"{health['at_risk_opportunities']['count']} 个商机存在逾期跟进或关键信息缺失"
                    ),
                    "action": "优先处理增强接口列出的风险商机 Top3",
                    "impact": health["at_risk_opportunities"]["total_amount"],
                }
            )
        if activity["impact"] > 0:
            insights.append(
                {
                    "type": "SUCCESS",
                    "title": "销售动作执行对预测有正向支撑",
                    "description": f"当前动作完成度评分 {activity['overall_score']}，对预测形成正向修正",
                    "action": "保持当前节奏，继续提高拜访和方案输出覆盖",
                    "impact": round(base_predicted * activity["impact"], 2),
                }
            )
        return insights

    def _build_recommendations(
        self,
        *,
        quality: Dict[str, Any],
        health: Dict[str, Any],
        activity: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        recommendations = []
        priority = 1

        if quality["dimensions"]:
            lowest_quality_dimension = min(
                quality["dimensions"],
                key=lambda item: item["score"],
            )
            recommendations.append(
                {
                    "priority": priority,
                    "action": f"优先提升{lowest_quality_dimension['name']}",
                    "description": lowest_quality_dimension["description"],
                    "expected_impact": f"{lowest_quality_dimension['score']} 分维度是当前短板",
                    "deadline": "本周内",
                    "responsible": "销售负责人/销售经理",
                }
            )
            priority += 1

        if health["at_risk_opportunities"]["count"] > 0:
            recommendations.append(
                {
                    "priority": priority,
                    "action": "处理高风险商机",
                    "description": "按金额优先处理超过 14 天未跟进、决策链缺失或预计成交逾期的商机",
                    "expected_impact": f"涉及金额 {health['at_risk_opportunities']['total_amount']}",
                    "deadline": "48 小时内",
                    "responsible": "对应销售",
                }
            )
            priority += 1

        if activity["metrics"]["visits_completion"] < 100 or activity["metrics"]["proposals_completion"] < 100:
            recommendations.append(
                {
                    "priority": priority,
                    "action": "补齐拜访和方案动作",
                    "description": "围绕活跃商机把拜访、会议和方案输出动作补到基线以上",
                    "expected_impact": "提高商机温度并提升预测稳定性",
                    "deadline": "本月内",
                    "responsible": "销售团队",
                }
            )

        return recommendations

    def _calculate_attainment_accuracy(self, target_value: float, actual_value: float) -> float:
        if target_value <= 0:
            return 0.0
        deviation = abs(actual_value - target_value) / target_value * 100
        return round(max(0.0, 100 - deviation), 1)

    def _get_user_prediction_accuracy(self, user_id: int, quality_score: float) -> tuple[float, str]:
        current_month_label = f"{date.today().year}-{date.today().month:02d}"
        targets = (
            self.db.query(SalesTarget)
            .filter(
                SalesTarget.target_scope == "PERSONAL",
                SalesTarget.user_id == user_id,
                SalesTarget.target_type == "CONTRACT_AMOUNT",
                SalesTarget.target_period == "MONTHLY",
                SalesTarget.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .order_by(SalesTarget.period_value.desc())
            .all()
        )
        valid_targets = [target for target in targets if (target.period_value or "") < current_month_label][:3]
        accuracies = []
        for target in valid_targets:
            result = self.target_performance_service.calculate_target(target)
            accuracies.append(
                self._calculate_attainment_accuracy(
                    float(target.target_value or 0),
                    float(result["actual_value"] or 0),
                )
            )

        if accuracies:
            return round(mean(accuracies), 1), "target_attainment_proxy"

        estimated = round(min(98.0, max(60.0, quality_score * 0.95)), 1)
        return estimated, "estimated_from_data_quality"

    def _get_user_win_rate(self, user_id: int) -> float:
        closed_opportunities = (
            self.db.query(Opportunity)
            .filter(
                Opportunity.owner_id == user_id,
                Opportunity.stage.in_(self.CLOSED_OPPORTUNITY_STAGES),
            )
            .all()
        )
        if not closed_opportunities:
            return 0.0
        won_count = sum(
            1
            for opportunity in closed_opportunities
            if opportunity.stage == OpportunityStageEnum.WON.value
        )
        return round(won_count / len(closed_opportunities) * 100, 1)

    def _get_user_sales_cycle_days(self, user_id: int) -> float:
        rows = (
            self.db.query(Lead.created_at, Contract.signing_date)
            .join(Opportunity, Opportunity.lead_id == Lead.id)
            .join(Contract, Contract.opportunity_id == Opportunity.id)
            .filter(
                Lead.owner_id == user_id,
                Lead.created_at.isnot(None),
                Contract.signing_date.isnot(None),
                Contract.status.in_(SalesForecastService.VALID_CONTRACT_STATUSES),
            )
            .all()
        )
        cycle_days = []
        for created_at, signing_date in rows:
            if not created_at or not signing_date:
                continue
            delta = (signing_date - created_at.date()).days
            if delta >= 0:
                cycle_days.append(delta)
        return round(mean(cycle_days), 1) if cycle_days else 0.0

    def _build_accuracy_band(
        self,
        description: str,
        profiles: List[Dict[str, Any]],
        characteristics: List[str],
    ) -> Dict[str, Any]:
        if not profiles:
            return {
                "description": description,
                "sales_count": 0,
                "avg_prediction_accuracy": 0.0,
                "avg_win_rate": 0.0,
                "avg_sales_cycle_days": 0.0,
                "characteristics": characteristics,
            }

        return {
            "description": description,
            "sales_count": len(profiles),
            "avg_prediction_accuracy": round(
                mean(profile["prediction_accuracy"] for profile in profiles),
                1,
            ),
            "avg_win_rate": round(mean(profile["win_rate"] for profile in profiles), 1),
            "avg_sales_cycle_days": round(
                mean(profile["sales_cycle_days"] for profile in profiles),
                1,
            ),
            "characteristics": characteristics,
        }


__all__ = ["SalesForecastEnhancementService"]
