# -*- coding: utf-8 -*-
"""
销售预测看板服务

将销售预测基础看板中的静态演示数据替换为真实业务数据。
"""

from datetime import date, datetime, time
from statistics import mean
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.common.date_range import get_month_range_by_ym
from app.models.enums.sales import OpportunityStageEnum
from app.models.project.customer import Customer
from app.models.sales import (
    Contract,
    Opportunity,
    SalesTarget,
    SalesTargetV2,
    SalesTeam,
    SalesTeamMember,
)
from app.models.user import User
from app.services.sales.forecast_enhancement_service import (
    PeriodContext,
    SalesForecastEnhancementService,
)


class SalesForecastDashboardService(SalesForecastEnhancementService):
    """销售预测基础看板服务。"""

    LEGACY_TARGET_ACTIVE_STATUSES = ("ACTIVE", "COMPLETED")

    def __init__(self, db: Session):
        super().__init__(db)

    def get_team_breakdown(self, period: str = "quarterly") -> Dict[str, Any]:
        """获取团队销售预测分解。"""
        period_context = self._get_period_context(period)
        teams = [
            self._build_team_forecast(team, period_context)
            for team in self._get_active_teams()
        ]

        teams.sort(
            key=lambda item: (
                item["predicted_completion"],
                item["predicted_revenue"],
                item["actual_revenue"],
            ),
            reverse=True,
        )
        previous_rank_map = self._build_previous_team_rank_map(period_context)

        for index, team in enumerate(teams, start=1):
            previous_rank = previous_rank_map.get(team["team_id"])
            team["rank"] = index
            team["rank_change"] = 0 if previous_rank is None else previous_rank - index

        return {
            "period": period_context.label,
            "period_type": period_context.period,
            "generated_at": date.today().isoformat(),
            "total_teams": len(teams),
            "teams_on_track": len(
                [team for team in teams if team["target_configured"] and team["predicted_completion"] >= 100]
            ),
            "teams_at_risk": len([team for team in teams if team["risk_level"] == "HIGH"]),
            "teams": teams,
        }

    def get_sales_rep_breakdown(
        self,
        team_id: Optional[int] = None,
        period: str = "quarterly",
    ) -> Dict[str, Any]:
        """获取个人销售预测分解。"""
        period_context = self._get_period_context(period)
        user_ids = (
            self._get_team_member_user_ids(team_id) if team_id else self._get_sales_user_ids()
        )
        reps = [
            self._build_sales_rep_forecast(user_id, period_context)
            for user_id in user_ids
        ]

        reps.sort(
            key=lambda item: (
                item["predicted_completion"],
                item["predicted_revenue"],
                item["actual_revenue"],
            ),
            reverse=True,
        )

        for index, rep in enumerate(reps, start=1):
            rep["rank"] = index

        return {
            "period": period_context.label,
            "period_type": period_context.period,
            "generated_at": date.today().isoformat(),
            "team_id": team_id,
            "total_reps": len(reps),
            "on_track_count": len(
                [rep for rep in reps if rep["target_configured"] and rep["predicted_completion"] >= 100]
            ),
            "at_risk_count": len(
                [rep for rep in reps if not rep["target_configured"] or rep["predicted_completion"] < 100]
            ),
            "sales_reps": reps,
        }

    def get_accuracy_tracking(self, months: int = 6) -> Dict[str, Any]:
        """获取最近 N 个月的预测准确性追踪。"""
        history = []
        skipped_periods = []

        for year, month in self._iter_recent_months(months):
            start_date, end_date = get_month_range_by_ym(year, month)
            target_value = self.forecast_service._get_sales_target(year, month, "monthly")
            target_source = self.forecast_service._get_target_source(year, month, "monthly")
            if target_value <= 0:
                skipped_periods.append(f"{year}-{month:02d}")
                continue

            actual_value = self.forecast_service._get_actual_revenue(
                datetime.combine(start_date, time.min),
                datetime.combine(end_date, time.min),
            )
            variance = round((actual_value - target_value) / target_value * 100, 1) if target_value else 0.0
            history.append(
                {
                    "period": f"{year}-{month:02d}",
                    "predicted": round(target_value, 2),
                    "actual": round(actual_value, 2),
                    "variance": variance,
                    "accuracy": self._calculate_attainment_accuracy(target_value, actual_value),
                    "prediction_source": target_source,
                }
            )

        history.sort(key=lambda item: item["period"])
        average_accuracy = round(mean(item["accuracy"] for item in history), 1) if history else 0.0

        return {
            "tracking_period": f"最近{months}个月",
            "average_accuracy": average_accuracy,
            "trend": self._calculate_accuracy_trend(history),
            "confidence_assessment": (
                "高" if average_accuracy > 95 else "中" if average_accuracy > 90 else "低"
            ),
            "history": history,
            "model_insights": self._build_accuracy_insights(history, skipped_periods),
            "prediction_method": "历史月度目标兑现度代理",
            "skipped_periods": skipped_periods,
        }

    def get_executive_dashboard(self) -> Dict[str, Any]:
        """获取领导驾驶舱数据。"""
        period_context = self._get_period_context("quarterly")
        company_forecast = self.forecast_service.get_company_forecast(period="quarterly")
        team_breakdown = self.get_team_breakdown(period="quarterly")
        new_customer_summary = self._build_new_customer_summary(period_context)
        avg_deal_size_summary = self._build_avg_deal_size_summary(period_context)

        return {
            "dashboard_date": date.today().isoformat(),
            "period": period_context.label,
            "kpi_summary": {
                "revenue": {
                    "target": round(float(company_forecast["targets"]["quarterly_target"]), 2),
                    "actual": round(float(company_forecast["targets"]["actual_revenue"]), 2),
                    "predicted": round(float(company_forecast["prediction"]["predicted_revenue"]), 2),
                    "completion_rate": round(float(company_forecast["targets"]["completion_rate"]), 2),
                    "predicted_completion": round(
                        float(company_forecast["prediction"]["predicted_completion_rate"]),
                        2,
                    ),
                    "status": self._completion_status(
                        float(company_forecast["targets"]["quarterly_target"]),
                        float(company_forecast["prediction"]["predicted_completion_rate"]),
                    ),
                    "target_source": company_forecast["target_source"],
                },
                "new_customers": new_customer_summary,
                "avg_deal_size": avg_deal_size_summary,
            },
            "traffic_lights": {
                "overall": self._map_risk_to_light(company_forecast["prediction"]["risk_level"]),
                "by_team": [
                    {
                        "team": team["team_name"],
                        "light": self._map_risk_to_light(team["risk_level"]),
                        "completion": team["predicted_completion"],
                    }
                    for team in team_breakdown["teams"]
                ],
            },
            "top_risks": self._build_executive_risks(company_forecast, team_breakdown["teams"]),
            "top_opportunities": self._build_executive_opportunities(period_context),
            "executive_actions": self._build_executive_actions(company_forecast, team_breakdown["teams"]),
            "trend_data": self._build_trend_data(period_context),
        }

    def _build_team_forecast(
        self,
        team: SalesTeam,
        period_context: PeriodContext,
    ) -> Dict[str, Any]:
        user_ids = self._get_team_member_user_ids(team.id)
        target_value, target_source = self._get_scoped_target_value(
            period_context,
            team_id=team.id,
        )
        actual_revenue = self._get_scope_actual_revenue(
            user_ids,
            period_context.start_date,
            period_context.end_date,
        )
        pipeline_data = self._get_scope_pipeline_analysis(user_ids, period_context)
        predicted_revenue = self._get_scope_predicted_revenue(actual_revenue, pipeline_data, period_context)
        completion_rate = round(actual_revenue / target_value * 100, 1) if target_value > 0 else 0.0
        predicted_completion = (
            round(predicted_revenue / target_value * 100, 1) if target_value > 0 else 0.0
        )
        previous_completion = self._get_previous_scope_completion(
            self._get_previous_period_context(period_context),
            team_id=team.id,
        )

        return {
            "team_id": team.id,
            "team_name": team.team_name,
            "manager": self._get_display_name(team.leader),
            "members_count": len(user_ids),
            "quarterly_target": round(target_value, 2),
            "actual_revenue": round(actual_revenue, 2),
            "completion_rate": completion_rate,
            "predicted_revenue": round(predicted_revenue, 2),
            "predicted_completion": predicted_completion,
            "confidence": self.forecast_service._calculate_confidence_level(pipeline_data),
            "risk_level": self._build_risk_level(target_value, predicted_completion),
            "trend": self._calculate_scope_trend(previous_completion, predicted_completion),
            "target_source": target_source,
            "target_configured": target_value > 0,
            "key_opportunities": self._get_scope_key_opportunities(user_ids, period_context),
            "alerts": self._build_scope_alerts(
                period_context=period_context,
                target_value=target_value,
                completion_rate=completion_rate,
                predicted_completion=predicted_completion,
                pipeline_data=pipeline_data,
            ),
        }

    def _build_sales_rep_forecast(
        self,
        user_id: int,
        period_context: PeriodContext,
    ) -> Dict[str, Any]:
        user = self.db.query(User).filter(User.id == user_id).first()
        team = self._get_user_primary_team(user_id)
        target_value, target_source = self._get_scoped_target_value(
            period_context,
            user_id=user_id,
        )
        actual_revenue = self._get_scope_actual_revenue(
            [user_id],
            period_context.start_date,
            period_context.end_date,
        )
        pipeline_data = self._get_scope_pipeline_analysis([user_id], period_context)
        predicted_revenue = self._get_scope_predicted_revenue(actual_revenue, pipeline_data, period_context)
        completion_rate = round(actual_revenue / target_value * 100, 1) if target_value > 0 else 0.0
        predicted_completion = (
            round(predicted_revenue / target_value * 100, 1) if target_value > 0 else 0.0
        )
        quality_profile = self._build_quality_profile(user_id)
        scope_alerts = self._build_scope_alerts(
            period_context=period_context,
            target_value=target_value,
            completion_rate=completion_rate,
            predicted_completion=predicted_completion,
            pipeline_data=pipeline_data,
        )

        return {
            "sales_id": user_id,
            "sales_name": self._get_display_name(user),
            "team_id": team.id if team else None,
            "team": team.team_name if team else self._get_user_team_name(user),
            "quarterly_target": round(target_value, 2),
            "actual_revenue": round(actual_revenue, 2),
            "completion_rate": completion_rate,
            "predicted_revenue": round(predicted_revenue, 2),
            "predicted_completion": predicted_completion,
            "confidence": self._build_rep_confidence(pipeline_data, quality_profile["overall_score"]),
            "pipeline_value": round(float(pipeline_data.get("total_amount", 0.0)), 2),
            "weighted_pipeline": round(float(pipeline_data.get("total_weighted", 0.0)), 2),
            "key_deals": self._get_scope_key_deals([user_id], period_context),
            "performance_trend": self._build_rep_performance_trend(predicted_completion),
            "target_source": target_source,
            "target_configured": target_value > 0,
            "alerts": list(dict.fromkeys((quality_profile["alerts"] + scope_alerts)))[:3],
        }

    def _get_active_teams(self) -> List[SalesTeam]:
        return (
            self.db.query(SalesTeam)
            .filter(SalesTeam.is_active.is_(True))
            .order_by(SalesTeam.sort_order.asc(), SalesTeam.id.asc())
            .all()
        )

    def _build_previous_team_rank_map(self, period_context: PeriodContext) -> Dict[int, int]:
        previous_context = self._get_previous_period_context(period_context)
        scores = []
        for team in self._get_active_teams():
            completion = self._get_previous_scope_completion(previous_context, team_id=team.id)
            scores.append((team.id, completion))

        scores.sort(key=lambda item: item[1], reverse=True)
        return {team_id: index for index, (team_id, _score) in enumerate(scores, start=1)}

    def _get_previous_scope_completion(
        self,
        period_context: PeriodContext,
        team_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> float:
        target_value, _target_source = self._get_scoped_target_value(
            period_context,
            team_id=team_id,
            user_id=user_id,
        )
        if team_id is not None:
            user_ids = self._get_team_member_user_ids(team_id)
        else:
            user_ids = [user_id] if user_id is not None else []
        actual_revenue = self._get_scope_actual_revenue(
            user_ids,
            period_context.start_date,
            period_context.end_date,
        )
        if target_value <= 0:
            return 0.0
        return round(actual_revenue / target_value * 100, 1)

    def _build_risk_level(self, target_value: float, predicted_completion: float) -> str:
        if target_value <= 0:
            return "MEDIUM"
        return self.forecast_service._assess_risk(0.0, predicted_completion, {"total_weighted": 0.0})

    def _calculate_scope_trend(self, previous_completion: float, current_completion: float) -> str:
        if previous_completion == 0:
            return "stable"
        if current_completion > previous_completion + 5:
            return "up"
        if current_completion < previous_completion - 5:
            return "down"
        return "stable"

    def _build_scope_alerts(
        self,
        *,
        period_context: PeriodContext,
        target_value: float,
        completion_rate: float,
        predicted_completion: float,
        pipeline_data: Dict[str, Any],
    ) -> List[str]:
        alerts = []
        time_progress = self._calculate_time_progress(period_context)

        if target_value <= 0:
            alerts.append("当前周期未配置销售目标")
        elif completion_rate + 5 < time_progress:
            alerts.append(f"完成率落后时间进度 {round(time_progress - completion_rate, 1)}%")

        if target_value > 0 and predicted_completion < 100:
            alerts.append(f"预测完成率仅 {round(predicted_completion, 1)}%，需要加速成交")

        total_weighted = float(pipeline_data.get("total_weighted", 0.0))
        high_stage_weighted = (
            float(pipeline_data.get("NEGOTIATION", {}).get("weighted_amount", 0.0))
            + float(pipeline_data.get("CLOSING", {}).get("weighted_amount", 0.0))
        )
        if total_weighted > 0 and high_stage_weighted / total_weighted < 0.3:
            alerts.append("高阶段商机储备不足")

        return alerts[:3]

    def _calculate_time_progress(self, period_context: PeriodContext) -> float:
        elapsed = (datetime.now().date() - period_context.start_date).days
        total = max(1, (period_context.end_date - period_context.start_date).days)
        return round(min(100.0, max(0.0, elapsed / total * 100)), 1)

    def _get_scope_actual_revenue(
        self,
        user_ids: Sequence[int],
        start_date: date,
        end_date: date,
    ) -> float:
        if not user_ids:
            return 0.0

        total = (
            self.db.query(func.coalesce(func.sum(Contract.total_amount), 0))
            .filter(
                Contract.sales_owner_id.in_(list(user_ids)),
                Contract.signing_date.isnot(None),
                Contract.signing_date >= start_date,
                Contract.signing_date <= end_date,
                Contract.status.in_(self.forecast_service.VALID_CONTRACT_STATUSES),
            )
            .scalar()
        )
        return round(float(total or 0.0), 2)

    def _get_scope_pipeline_analysis(
        self,
        user_ids: Sequence[int],
        period_context: PeriodContext,
    ) -> Dict[str, Any]:
        pipeline = {
            stage.name: {
                "count": 0,
                "total_amount": 0.0,
                "weighted_amount": 0.0,
                "win_rate": self.forecast_service.STAGE_WIN_RATES.get(stage, 0.5) * 100,
            }
            for stage in OpportunityStageEnum
            if stage.value in self.ACTIVE_OPPORTUNITY_STAGES
        }
        if not user_ids:
            pipeline["total_weighted"] = 0.0
            pipeline["total_amount"] = 0.0
            return pipeline

        rows = (
            self.db.query(
                Opportunity.stage,
                func.count(Opportunity.id),
                func.coalesce(func.sum(Opportunity.est_amount), 0),
            )
            .filter(
                Opportunity.owner_id.in_(list(user_ids)),
                Opportunity.stage.in_(self.ACTIVE_OPPORTUNITY_STAGES),
                Opportunity.est_amount.isnot(None),
                or_(
                    Opportunity.expected_close_date.is_(None),
                    and_(
                        Opportunity.expected_close_date >= period_context.start_date,
                        Opportunity.expected_close_date <= period_context.end_date,
                    ),
                ),
            )
            .group_by(Opportunity.stage)
            .all()
        )

        total_weighted = 0.0
        total_amount = 0.0
        for stage_value, count, amount_raw in rows:
            stage = OpportunityStageEnum(stage_value)
            amount = float(amount_raw or 0.0)
            win_rate = self.forecast_service.STAGE_WIN_RATES.get(stage, 0.5)
            weighted_amount = amount * win_rate
            total_amount += amount
            total_weighted += weighted_amount
            pipeline[stage.name] = {
                "count": int(count),
                "total_amount": round(amount, 2),
                "weighted_amount": round(weighted_amount, 2),
                "win_rate": round(win_rate * 100, 1),
            }

        pipeline["total_amount"] = round(total_amount, 2)
        pipeline["total_weighted"] = round(total_weighted, 2)
        return pipeline

    def _get_scope_predicted_revenue(
        self,
        actual_revenue: float,
        pipeline_data: Dict[str, Any],
        period_context: PeriodContext,
    ) -> float:
        return round(
            self.forecast_service._calculate_predicted_revenue(
                actual_revenue,
                pipeline_data,
                datetime.combine(period_context.start_date, time.min),
                datetime.combine(period_context.end_date, time.min),
            ),
            2,
        )

    def _get_scope_key_opportunities(
        self,
        user_ids: Sequence[int],
        period_context: PeriodContext,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        opportunities = self._get_scope_opportunities(user_ids, period_context)
        items = []
        for opportunity in opportunities[:limit]:
            items.append(
                {
                    "name": opportunity.opp_name,
                    "amount": round(float(opportunity.est_amount or 0.0), 2),
                    "stage": opportunity.stage,
                }
            )
        return items

    def _get_scope_key_deals(
        self,
        user_ids: Sequence[int],
        period_context: PeriodContext,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        opportunities = self._get_scope_opportunities(user_ids, period_context)
        items = []
        for opportunity in opportunities[:limit]:
            probability = opportunity.probability or round(
                self.forecast_service.STAGE_WIN_RATES.get(
                    OpportunityStageEnum(opportunity.stage),
                    0.5,
                )
                * 100
            )
            items.append(
                {
                    "customer": self._get_customer_name(opportunity.customer),
                    "amount": round(float(opportunity.est_amount or 0.0), 2),
                    "probability": int(probability),
                }
            )
        return items

    def _get_scope_opportunities(
        self,
        user_ids: Sequence[int],
        period_context: PeriodContext,
    ) -> List[Opportunity]:
        if not user_ids:
            return []

        opportunities = (
            self.db.query(Opportunity)
            .filter(
                Opportunity.owner_id.in_(list(user_ids)),
                Opportunity.stage.in_(self.ACTIVE_OPPORTUNITY_STAGES),
                Opportunity.est_amount.isnot(None),
                or_(
                    Opportunity.expected_close_date.is_(None),
                    and_(
                        Opportunity.expected_close_date >= period_context.start_date,
                        Opportunity.expected_close_date <= period_context.end_date,
                    ),
                ),
            )
            .all()
        )

        return sorted(
            opportunities,
            key=lambda item: float(item.est_amount or 0.0)
            * self.forecast_service.STAGE_WIN_RATES.get(OpportunityStageEnum(item.stage), 0.5),
            reverse=True,
        )

    def _build_rep_confidence(self, pipeline_data: Dict[str, Any], quality_score: float) -> int:
        pipeline_confidence = self.forecast_service._calculate_confidence_level(pipeline_data)
        return max(50, min(100, int(round((pipeline_confidence + quality_score) / 2))))

    def _build_rep_performance_trend(self, predicted_completion: float) -> str:
        if predicted_completion >= 110:
            return "excellent"
        if predicted_completion >= 100:
            return "good"
        if predicted_completion >= 85:
            return "stable"
        return "at_risk"

    def _get_team_member_user_ids(self, team_id: Optional[int]) -> List[int]:
        if team_id is None:
            return []

        rows = (
            self.db.query(
                SalesTeamMember.user_id,
                SalesTeamMember.is_primary,
            )
            .filter(
                SalesTeamMember.team_id == team_id,
                SalesTeamMember.is_active.is_(True),
            )
            .all()
        )

        user_ids = sorted({user_id for user_id, _is_primary in rows})
        if user_ids:
            primary_user_ids = {user_id for user_id, is_primary in rows if is_primary}
            if not primary_user_ids:
                return user_ids

            primary_users_in_other_teams = {
                user_id
                for user_id, in self.db.query(SalesTeamMember.user_id)
                .filter(
                    SalesTeamMember.user_id.in_(user_ids),
                    SalesTeamMember.team_id != team_id,
                    SalesTeamMember.is_active.is_(True),
                    SalesTeamMember.is_primary.is_(True),
                )
                .distinct()
                .all()
            }
            resolved_user_ids = primary_user_ids | {
                user_id for user_id in user_ids if user_id not in primary_users_in_other_teams
            }
            return sorted(resolved_user_ids)

        team = self.db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
        if team and team.leader_id:
            return [team.leader_id]
        return []

    def _get_user_primary_team(self, user_id: int) -> Optional[SalesTeam]:
        membership = (
            self.db.query(SalesTeamMember, SalesTeam)
            .join(SalesTeam, SalesTeam.id == SalesTeamMember.team_id)
            .filter(
                SalesTeamMember.user_id == user_id,
                SalesTeamMember.is_active.is_(True),
                SalesTeam.is_active.is_(True),
            )
            .order_by(SalesTeamMember.is_primary.desc(), SalesTeamMember.id.asc())
            .first()
        )
        if membership:
            _member, team = membership
            return team
        return None

    def _get_scoped_target_value(
        self,
        period_context: PeriodContext,
        *,
        team_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> tuple[float, str]:
        year, period_index = self._get_period_position(period_context)
        exact_v2 = self._get_exact_v2_target(period_context.period, year, period_index, team_id, user_id)
        if exact_v2 > 0:
            return round(exact_v2, 2), "sales_targets_v2"

        exact_legacy = self._get_exact_legacy_target(period_context, team_id=team_id, user_id=user_id)
        if exact_legacy > 0:
            return round(exact_legacy, 2), "sales_targets"

        annual_v2 = self._get_exact_v2_target("yearly", year, 1, team_id, user_id)
        annual_legacy = self._get_exact_legacy_target(
            self._build_period_context("yearly", year, 1),
            team_id=team_id,
            user_id=user_id,
        )
        annual_target = annual_v2 or annual_legacy
        if annual_target > 0:
            if period_context.period == "quarterly":
                return round(
                    self.forecast_service._derive_quarter_target_from_annual(annual_target, period_index),
                    2,
                ), "derived_from_year_target"
            if period_context.period == "monthly":
                quarter_target = self._get_exact_v2_target(
                    "quarterly",
                    year,
                    self.forecast_service._month_to_quarter(period_index),
                    team_id,
                    user_id,
                ) or self._get_exact_legacy_target(
                    self._build_period_context(
                        "quarterly",
                        year,
                        self.forecast_service._month_to_quarter(period_index),
                    ),
                    team_id=team_id,
                    user_id=user_id,
                )
                if quarter_target > 0:
                    return round(
                        self.forecast_service._derive_month_target_from_quarter(
                            quarter_target,
                            period_index,
                        ),
                        2,
                    ), "derived_from_quarter_target"
                return round(
                    self.forecast_service._derive_month_target_from_annual(annual_target, period_index),
                    2,
                ), "derived_from_year_target"
            return round(annual_target, 2), "sales_targets_v2" if annual_v2 else "sales_targets"

        return 0.0, "no_target_configured"

    def _get_exact_v2_target(
        self,
        period: str,
        year: int,
        period_index: int,
        team_id: Optional[int],
        user_id: Optional[int],
    ) -> float:
        query = self.db.query(func.coalesce(func.sum(SalesTargetV2.sales_target), 0)).filter(
            SalesTargetV2.target_year == year
        )

        if user_id is not None:
            query = query.filter(
                SalesTargetV2.target_type == "personal",
                SalesTargetV2.user_id == user_id,
            )
        elif team_id is not None:
            query = query.filter(
                SalesTargetV2.target_type == "team",
                SalesTargetV2.team_id == team_id,
            )
        else:
            return 0.0

        if period == "yearly":
            query = query.filter(SalesTargetV2.target_period == "year")
        elif period == "quarterly":
            query = query.filter(
                SalesTargetV2.target_period == "quarter",
                SalesTargetV2.target_quarter == period_index,
            )
        else:
            query = query.filter(
                SalesTargetV2.target_period == "month",
                SalesTargetV2.target_month == period_index,
            )

        return float(query.scalar() or 0.0)

    def _get_exact_legacy_target(
        self,
        period_context: PeriodContext,
        *,
        team_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> float:
        target_period, period_value = self.forecast_service._build_legacy_target_period(
            period_context.start_date.year,
            self._get_period_position(period_context)[1],
            period_context.period,
        )
        query = self.db.query(func.coalesce(func.sum(SalesTarget.target_value), 0)).filter(
            SalesTarget.target_type == "CONTRACT_AMOUNT",
            SalesTarget.target_period == target_period,
            SalesTarget.period_value == period_value,
            SalesTarget.status.in_(self.LEGACY_TARGET_ACTIVE_STATUSES),
        )

        if user_id is not None:
            query = query.filter(
                SalesTarget.target_scope == "PERSONAL",
                SalesTarget.user_id == user_id,
            )
        elif team_id is not None:
            query = query.filter(
                SalesTarget.target_scope == "TEAM",
                SalesTarget.team_id == team_id,
            )
        else:
            return 0.0

        return float(query.scalar() or 0.0)

    def _build_period_context(self, period: str, year: int, period_index: int) -> PeriodContext:
        normalized_period = (period or "monthly").lower()
        if normalized_period == "yearly":
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            label = str(year)
            scale = 12
        elif normalized_period == "quarterly":
            start_month = (period_index - 1) * 3 + 1
            start_date, _ = get_month_range_by_ym(year, start_month)
            _, end_date = get_month_range_by_ym(year, start_month + 2)
            label = f"{year}-Q{period_index}"
            scale = 3
        else:
            start_date, end_date = get_month_range_by_ym(year, period_index)
            label = f"{year}-{period_index:02d}"
            scale = 1

        return PeriodContext(
            period=normalized_period,
            label=label,
            start_date=start_date,
            end_date=end_date,
            start_dt=datetime.combine(start_date, time.min),
            end_exclusive=datetime.combine(end_date, time.max),
            scale=scale,
        )

    def _get_period_position(self, period_context: PeriodContext) -> tuple[int, int]:
        if period_context.period == "yearly":
            return period_context.start_date.year, 1
        if period_context.period == "quarterly":
            return period_context.start_date.year, (period_context.start_date.month - 1) // 3 + 1
        return period_context.start_date.year, period_context.start_date.month

    def _get_previous_period_context(self, period_context: PeriodContext) -> PeriodContext:
        year, period_index = self._get_period_position(period_context)
        previous_year, previous_index = self.forecast_service._shift_period(
            year,
            period_index,
            period_context.period,
            -1,
        )
        return self._build_period_context(period_context.period, previous_year, previous_index)

    def _iter_recent_months(self, months: int) -> List[tuple[int, int]]:
        results = []
        year = date.today().year
        month = date.today().month
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1

        for _ in range(max(1, months)):
            results.append((year, month))
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1

        return results

    def _calculate_accuracy_trend(self, history: List[Dict[str, Any]]) -> str:
        if len(history) < 2:
            return "stable"
        delta = history[-1]["accuracy"] - history[0]["accuracy"]
        if delta > 2:
            return "up"
        if delta < -2:
            return "down"
        return "stable"

    def _build_accuracy_insights(
        self,
        history: List[Dict[str, Any]],
        skipped_periods: List[str],
    ) -> List[str]:
        if not history:
            return ["暂无可用于评估预测准确率的历史目标数据"]

        avg_accuracy = round(mean(item["accuracy"] for item in history), 1)
        max_variance_item = max(history, key=lambda item: abs(item["variance"]))
        insights = [
            f"历史目标兑现度代理的平均准确率为 {avg_accuracy}%",
            (
                f"最大偏差出现在 {max_variance_item['period']}，偏差 {abs(max_variance_item['variance'])}%"
            ),
            "当前准确率追踪已改为真实历史目标与签约数据计算，不再返回固定演示值",
        ]
        if skipped_periods:
            insights.append(f"以下月份未配置目标，未纳入准确率统计：{', '.join(skipped_periods[:3])}")
        return insights

    def _completion_status(self, target: float, predicted_completion: float) -> str:
        if target <= 0:
            return "no_target"
        return "on_track" if predicted_completion >= 100 else "at_risk"

    def _map_risk_to_light(self, risk_level: str) -> str:
        mapping = {"LOW": "GREEN", "MEDIUM": "YELLOW", "HIGH": "RED"}
        return mapping.get(risk_level, "YELLOW")

    def _build_executive_risks(
        self,
        company_forecast: Dict[str, Any],
        teams: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        risks = []
        for risk in company_forecast.get("risks", []):
            risks.append(
                {
                    "risk": risk["risk"],
                    "impact": self._format_impact(risk.get("impact")),
                    "action": risk.get("mitigation") or "请销售管理层跟进",
                }
            )

        for team in teams:
            if team["risk_level"] == "HIGH":
                risks.append(
                    {
                        "risk": f"{team['team_name']}预测未达标",
                        "impact": f"预测完成率 {team['predicted_completion']}%",
                        "action": team["alerts"][0] if team["alerts"] else "请区域负责人专项跟进",
                    }
                )

        deduped = []
        seen = set()
        for risk in risks:
            key = risk["risk"]
            if key in seen:
                continue
            seen.add(key)
            deduped.append(risk)
        return deduped[:3]

    def _build_executive_opportunities(self, period_context: PeriodContext) -> List[Dict[str, Any]]:
        user_ids = self._get_sales_user_ids()
        opportunities = self._get_scope_opportunities(user_ids, period_context)
        items = []
        for opportunity in opportunities[:3]:
            probability = opportunity.probability or round(
                self.forecast_service.STAGE_WIN_RATES.get(
                    OpportunityStageEnum(opportunity.stage),
                    0.5,
                )
                * 100
            )
            items.append(
                {
                    "customer": self._get_customer_name(opportunity.customer),
                    "amount": round(float(opportunity.est_amount or 0.0), 2),
                    "probability": int(probability),
                    "expected_close": (
                        opportunity.expected_close_date.isoformat()
                        if opportunity.expected_close_date
                        else None
                    ),
                }
            )
        return items

    def _build_executive_actions(
        self,
        company_forecast: Dict[str, Any],
        teams: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        actions = []
        for item in company_forecast.get("recommended_actions", []):
            actions.append(
                {
                    "priority": item.get("priority", len(actions) + 1),
                    "action": item["action"],
                    "reason": f"预计影响 {round(float(item.get('impact', 0.0)), 2)}",
                    "deadline": item.get("deadline") or "本周期内",
                }
            )

        for team in teams:
            if team["risk_level"] == "HIGH":
                actions.append(
                    {
                        "priority": len(actions) + 1,
                        "action": f"支持 {team['team_name']} 重点商机推进",
                        "reason": team["alerts"][0] if team["alerts"] else "团队预测未达标",
                        "deadline": "本周内",
                    }
                )

        actions.sort(key=lambda item: item["priority"])
        return actions[:3]

    def _build_trend_data(self, period_context: PeriodContext) -> List[Dict[str, Any]]:
        year = period_context.start_date.year
        start_month = period_context.start_date.month
        months = [start_month, start_month + 1, start_month + 2]
        current_month = date.today().month
        trend_data = []

        for month in months:
            start_date, end_date = get_month_range_by_ym(year, month)
            target_value = self.forecast_service._get_sales_target(year, month, "monthly")
            actual_value = self.forecast_service._get_actual_revenue(
                datetime.combine(start_date, time.min),
                datetime.combine(end_date, time.min),
            )
            if month == current_month:
                predicted_value = self.forecast_service.get_company_forecast(
                    period="monthly",
                    year=year,
                    quarter=month,
                )["prediction"]["predicted_revenue"]
            else:
                predicted_value = target_value if target_value > 0 else actual_value

            trend_data.append(
                {
                    "month": f"{month} 月",
                    "target": round(target_value, 2),
                    "actual": round(actual_value, 2),
                    "predicted": round(float(predicted_value), 2),
                }
            )

        return trend_data

    def _build_new_customer_summary(self, period_context: PeriodContext) -> Dict[str, Any]:
        actual = self._count_new_customers(period_context)
        predicted = round(actual + self._predict_new_customers(period_context), 1)
        target = 0.0
        completion_rate = round(actual / target * 100, 1) if target > 0 else 0.0
        predicted_completion = round(predicted / target * 100, 1) if target > 0 else 0.0

        return {
            "target": target,
            "actual": actual,
            "predicted": predicted,
            "completion_rate": completion_rate,
            "predicted_completion": predicted_completion,
            "status": self._completion_status(target, predicted_completion),
        }

    def _count_new_customers(self, period_context: PeriodContext) -> int:
        rows = (
            self.db.query(
                Contract.customer_id,
                func.min(Contract.signing_date).label("first_signing_date"),
            )
            .filter(
                Contract.customer_id.isnot(None),
                Contract.signing_date.isnot(None),
                Contract.status.in_(self.forecast_service.VALID_CONTRACT_STATUSES),
            )
            .group_by(Contract.customer_id)
            .all()
        )
        return sum(
            1
            for _customer_id, first_signing_date in rows
            if first_signing_date
            and period_context.start_date <= first_signing_date <= period_context.end_date
        )

    def _predict_new_customers(self, period_context: PeriodContext) -> float:
        existing_customer_ids = {
            customer_id
            for customer_id, in self.db.query(Contract.customer_id)
            .filter(
                Contract.customer_id.isnot(None),
                Contract.signing_date.isnot(None),
                Contract.signing_date < period_context.start_date,
                Contract.status.in_(self.forecast_service.VALID_CONTRACT_STATUSES),
            )
            .distinct()
            .all()
        }
        opportunities = (
            self.db.query(Opportunity)
            .filter(
                Opportunity.customer_id.isnot(None),
                Opportunity.customer_id.notin_(existing_customer_ids) if existing_customer_ids else True,
                Opportunity.stage.in_(self.ACTIVE_OPPORTUNITY_STAGES),
                Opportunity.est_amount.isnot(None),
                or_(
                    Opportunity.expected_close_date.is_(None),
                    and_(
                        Opportunity.expected_close_date >= period_context.start_date,
                        Opportunity.expected_close_date <= period_context.end_date,
                    ),
                ),
            )
            .all()
        )

        customer_probability_map: Dict[int, float] = {}
        for opportunity in opportunities:
            probability = opportunity.probability or (
                self.forecast_service.STAGE_WIN_RATES.get(
                    OpportunityStageEnum(opportunity.stage),
                    0.5,
                )
                * 100
            )
            customer_probability_map[opportunity.customer_id] = max(
                customer_probability_map.get(opportunity.customer_id, 0.0),
                float(probability),
            )

        return round(sum(probability / 100 for probability in customer_probability_map.values()), 1)

    def _build_avg_deal_size_summary(self, period_context: PeriodContext) -> Dict[str, Any]:
        actual = self._get_average_deal_size(period_context)
        previous_context = self._get_previous_period_context(period_context)
        previous_actual = self._get_average_deal_size(previous_context)
        change_percentage = (
            round((actual - previous_actual) / previous_actual * 100, 1)
            if previous_actual > 0
            else 0.0
        )

        return {
            "target": 0.0,
            "actual": round(actual, 2),
            "trend": "up" if change_percentage > 2 else "down" if change_percentage < -2 else "stable",
            "change_percentage": change_percentage,
        }

    def _get_average_deal_size(self, period_context: PeriodContext) -> float:
        rows = (
            self.db.query(
                func.coalesce(func.sum(Contract.total_amount), 0),
                func.count(Contract.id),
            )
            .filter(
                Contract.signing_date.isnot(None),
                Contract.signing_date >= period_context.start_date,
                Contract.signing_date <= period_context.end_date,
                Contract.status.in_(self.forecast_service.VALID_CONTRACT_STATUSES),
            )
            .first()
        )
        total_amount = float(rows[0] or 0.0) if rows else 0.0
        contract_count = int(rows[1] or 0) if rows else 0
        if contract_count <= 0:
            return 0.0
        return round(total_amount / contract_count, 2)

    def _format_impact(self, impact: Optional[Any]) -> str:
        if impact is None:
            return "影响待评估"
        numeric_impact = float(impact)
        if numeric_impact == int(numeric_impact):
            numeric_impact = int(numeric_impact)
        return f"{numeric_impact}"

    def _get_customer_name(self, customer: Optional[Customer]) -> str:
        if customer and customer.customer_name:
            return customer.customer_name
        return "未命名客户"


__all__ = ["SalesForecastDashboardService"]
