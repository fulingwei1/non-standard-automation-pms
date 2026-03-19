# -*- coding: utf-8 -*-
"""
销售预测服务 - 基于真实数据的 AI 预测

提供：
1. 公司整体销售预测
2. 团队/个人预测分解
3. 预测准确性追踪
4. 风险预警
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.sales import SalesTarget, SalesTargetV2
from app.models.sales.leads import Opportunity
from app.models.sales.contracts import Contract
from app.models.project.customer import Customer
from app.models.enums.sales import OpportunityStageEnum

logger = logging.getLogger(__name__)


class SalesForecastService:
    """销售预测服务类"""

    ACTIVE_PIPELINE_STAGES = (
        OpportunityStageEnum.DISCOVERY.value,
        OpportunityStageEnum.QUALIFICATION.value,
        OpportunityStageEnum.PROPOSAL.value,
        OpportunityStageEnum.NEGOTIATION.value,
        OpportunityStageEnum.CLOSING.value,
    )
    VALID_CONTRACT_STATUSES = (
        "SIGNED",
        "signed",
        "ACTIVE",
        "active",
        "EXECUTING",
        "executing",
        "COMPLETED",
        "completed",
    )

    # 赢单率基准（按商机阶段）
    STAGE_WIN_RATES = {
        OpportunityStageEnum.DISCOVERY: 0.15,        # 初步接触
        OpportunityStageEnum.QUALIFICATION: 0.30,    # 需求挖掘
        OpportunityStageEnum.PROPOSAL: 0.50,         # 方案介绍
        OpportunityStageEnum.NEGOTIATION: 0.70,      # 价格谈判
        OpportunityStageEnum.CLOSING: 0.85,          # 成交促成
    }

    # 季节性因子（月度）
    SEASONAL_FACTORS = {
        1: 0.7,   # 1 月：春节影响
        2: 0.8,   # 2 月：春节影响
        3: 1.1,   # 3 月：Q1 冲刺
        4: 1.0,   # 4 月：正常
        5: 1.1,   # 5 月：正常
        6: 1.2,   # 6 月：Q2 冲刺
        7: 0.9,   # 7 月：淡季
        8: 0.9,   # 8 月：淡季
        9: 1.1,   # 9 月：Q3 冲刺
        10: 1.0,  # 10 月：正常
        11: 1.1,  # 11 月：正常
        12: 1.3,  # 12 月：Q4 冲刺
    }

    def __init__(self, db: Session):
        self.db = db

    def get_company_forecast(
        self,
        period: str = "quarterly",
        year: Optional[int] = None,
        quarter: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取公司整体销售预测

        Args:
            period: 周期类型 (monthly/quarterly/yearly)
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            预测数据字典
        """
        if year is None:
            year = datetime.now().year
        if quarter is None:
            quarter = (datetime.now().month - 1) // 3 + 1

        # 计算周期日期范围
        start_date, end_date = self._get_period_dates(year, quarter, period)

        # 1. 获取销售目标（优先读取数据库目标）
        target = self._get_sales_target(year, quarter, period)

        # 2. 获取已完成业绩（已签约合同）
        actual_revenue = self._get_actual_revenue(start_date, end_date)

        # 3. 获取漏斗中商机及预测
        pipeline_data = self._get_pipeline_analysis(start_date, end_date)

        # 4. 计算预测收入
        predicted_revenue = self._calculate_predicted_revenue(
            actual_revenue, pipeline_data, start_date, end_date
        )

        # 5. 计算完成率和预测完成率
        completion_rate = (actual_revenue / target * 100) if target > 0 else 0
        predicted_completion = (predicted_revenue / target * 100) if target > 0 else 0

        # 6. 计算置信区间
        confidence_interval = self._calculate_confidence_interval(predicted_revenue, pipeline_data)

        # 7. 风险评估
        risk_level = self._assess_risk(completion_rate, predicted_completion, pipeline_data)

        # 8. 历史对比
        historical_comparison = self._get_historical_comparison(year, quarter, period)

        return {
            "period": f"{year}-Q{quarter}" if period == "quarterly" else f"{year}-{quarter:02d}",
            "period_type": period,
            "generated_at": date.today().isoformat(),
            "target_source": self._get_target_source(year, quarter, period),
            "targets": {
                "quarterly_target": target,
                "actual_revenue": actual_revenue,
                "completion_rate": round(completion_rate, 1),
                "days_elapsed": max(0, (datetime.now() - start_date).days),
                "total_days": max(1, (end_date - start_date).days),
                "time_progress": round(
                    min(
                        100.0,
                        max(0.0, (datetime.now() - start_date).days / max(1, (end_date - start_date).days) * 100),
                    ),
                    1,
                ),
            },
            "prediction": {
                "predicted_revenue": predicted_revenue,
                "predicted_completion_rate": round(predicted_completion, 1),
                "confidence_level": self._calculate_confidence_level(pipeline_data),
                "confidence_interval": confidence_interval,
                "risk_level": risk_level,
                "trend": self._calculate_trend(historical_comparison, predicted_completion),
            },
            "funnel_contribution": pipeline_data,
            "forecast_breakdown": self._get_forecast_breakdown(actual_revenue, pipeline_data),
            "key_drivers": self._identify_key_drivers(
                pipeline_data,
                actual_revenue,
                target,
                start_date,
                end_date,
            ),
            "risks": self._identify_risks(
                completion_rate,
                predicted_completion,
                pipeline_data,
                target,
                start_date,
                end_date,
            ),
            "recommended_actions": self._generate_recommendations(
                pipeline_data,
                risk_level,
                start_date,
                end_date,
            ),
            "historical_comparison": historical_comparison,
        }

    def _get_period_dates(
        self, year: int, quarter: int, period: str
    ) -> tuple[datetime, datetime]:
        """获取周期日期范围"""
        if period == "yearly":
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        elif period == "quarterly":
            month_start = (quarter - 1) * 3 + 1
            start_date = datetime(year, month_start, 1)
            if quarter == 4:
                end_date = datetime(year, 12, 31)
            else:
                end_date = datetime(year, month_start + 3, 1) - timedelta(days=1)
        else:  # monthly
            start_date = datetime(year, quarter, 1)
            if quarter == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, quarter + 1, 1) - timedelta(days=1)

        return start_date, end_date

    def _get_sales_target(self, year: int, quarter: int, period: str) -> float:
        """获取销售目标"""
        direct_target = self._get_v2_sales_target(year, quarter, period)
        if direct_target > 0:
            return direct_target

        legacy_target = self._get_legacy_sales_target(year, quarter, period)
        if legacy_target > 0:
            return legacy_target

        annual_target = (
            self._get_v2_sales_target(year, 1, "yearly")
            or self._get_legacy_sales_target(year, 1, "yearly")
        )
        if annual_target <= 0:
            return 0.0

        if period == "yearly":
            return annual_target
        if period == "quarterly":
            return self._derive_quarter_target_from_annual(annual_target, quarter)
        if period == "monthly":
            quarterly_target = self._get_v2_sales_target(
                year, self._month_to_quarter(quarter), "quarterly"
            ) or self._get_legacy_sales_target(year, self._month_to_quarter(quarter), "quarterly")
            if quarterly_target > 0:
                return self._derive_month_target_from_quarter(quarterly_target, quarter)
            return self._derive_month_target_from_annual(annual_target, quarter)
        return 0.0

    def _get_target_source(self, year: int, quarter: int, period: str) -> str:
        """返回预测目标来源，方便前端识别数据真实性。"""
        if self._get_v2_sales_target(year, quarter, period) > 0:
            return "sales_targets_v2"
        if self._get_legacy_sales_target(year, quarter, period) > 0:
            return "sales_targets"
        annual_target = (
            self._get_v2_sales_target(year, 1, "yearly")
            or self._get_legacy_sales_target(year, 1, "yearly")
        )
        if annual_target > 0:
            return "derived_from_year_target"
        return "no_target_configured"

    def _get_v2_sales_target(self, year: int, period_index: int, period: str) -> float:
        normalized_period = (period or "quarterly").lower()
        base_query = self.db.query(func.coalesce(func.sum(SalesTargetV2.sales_target), 0)).filter(
            SalesTargetV2.target_year == year
        )

        if normalized_period == "yearly":
            period_query = base_query.filter(SalesTargetV2.target_period == "year")
        elif normalized_period == "quarterly":
            period_query = base_query.filter(
                SalesTargetV2.target_period == "quarter",
                SalesTargetV2.target_quarter == period_index,
            )
        else:
            period_query = base_query.filter(
                SalesTargetV2.target_period == "month",
                SalesTargetV2.target_month == period_index,
            )

        for target_type in ("company", "team", "personal"):
            total = period_query.filter(SalesTargetV2.target_type == target_type).scalar() or 0
            if total:
                return float(total)
        return 0.0

    def _get_legacy_sales_target(self, year: int, period_index: int, period: str) -> float:
        target_period, period_value = self._build_legacy_target_period(year, period_index, period)
        rows = (
            self.db.query(
                SalesTarget.target_scope,
                func.coalesce(func.sum(SalesTarget.target_value), 0).label("target_total"),
            )
            .filter(
                SalesTarget.target_type == "CONTRACT_AMOUNT",
                SalesTarget.target_period == target_period,
                SalesTarget.period_value == period_value,
                SalesTarget.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .group_by(SalesTarget.target_scope)
            .all()
        )
        target_map = {scope: float(total or 0) for scope, total in rows}
        for scope in ("DEPARTMENT", "TEAM", "PERSONAL"):
            if target_map.get(scope):
                return target_map[scope]
        return 0.0

    @staticmethod
    def _build_legacy_target_period(year: int, period_index: int, period: str) -> tuple[str, str]:
        normalized_period = (period or "quarterly").lower()
        if normalized_period == "yearly":
            return "YEARLY", str(year)
        if normalized_period == "quarterly":
            return "QUARTERLY", f"{year}-Q{period_index}"
        return "MONTHLY", f"{year}-{period_index:02d}"

    @staticmethod
    def _month_to_quarter(month: int) -> int:
        return (month - 1) // 3 + 1

    def _derive_quarter_target_from_annual(self, annual_target: float, quarter: int) -> float:
        months = [(quarter - 1) * 3 + 1, (quarter - 1) * 3 + 2, (quarter - 1) * 3 + 3]
        annual_factor = sum(self.SEASONAL_FACTORS.values())
        quarter_factor = sum(self.SEASONAL_FACTORS.get(month, 1.0) for month in months)
        return annual_target * (quarter_factor / annual_factor) if annual_factor > 0 else 0.0

    def _derive_month_target_from_annual(self, annual_target: float, month: int) -> float:
        annual_factor = sum(self.SEASONAL_FACTORS.values())
        month_factor = self.SEASONAL_FACTORS.get(month, 1.0)
        return annual_target * (month_factor / annual_factor) if annual_factor > 0 else 0.0

    def _derive_month_target_from_quarter(self, quarterly_target: float, month: int) -> float:
        quarter = self._month_to_quarter(month)
        months = [(quarter - 1) * 3 + 1, (quarter - 1) * 3 + 2, (quarter - 1) * 3 + 3]
        quarter_factor = sum(self.SEASONAL_FACTORS.get(value, 1.0) for value in months)
        month_factor = self.SEASONAL_FACTORS.get(month, 1.0)
        return quarterly_target * (month_factor / quarter_factor) if quarter_factor > 0 else 0.0

    def _get_actual_revenue(self, start_date: datetime, end_date: datetime) -> float:
        """获取已完成业绩（已签约合同金额）"""
        try:
            total = (
                self.db.query(func.coalesce(func.sum(Contract.total_amount), 0))
                .filter(
                    Contract.signing_date.isnot(None),
                    Contract.signing_date >= start_date.date(),
                    Contract.signing_date <= end_date.date(),
                    Contract.status.in_(self.VALID_CONTRACT_STATUSES),
                )
                .scalar()
            )
            return float(total) if total else 0.0
        except Exception as e:
            logger.error(f"获取实际业绩失败：{e}")
            return 0.0

    def _get_pipeline_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取漏斗分析数据"""
        try:
            pipeline = {
                stage.name: {
                    "count": 0,
                    "total_amount": 0.0,
                    "weighted_amount": 0.0,
                    "win_rate": self.STAGE_WIN_RATES.get(stage, 0.5) * 100,
                }
                for stage in OpportunityStageEnum
                if stage.value in self.ACTIVE_PIPELINE_STAGES
            }
            total_weighted = 0.0

            rows = (
                self.db.query(
                    Opportunity.stage,
                    func.count(Opportunity.id),
                    func.coalesce(func.sum(Opportunity.est_amount), 0),
                )
                .filter(
                    Opportunity.stage.in_(self.ACTIVE_PIPELINE_STAGES),
                    Opportunity.est_amount.isnot(None),
                    or_(
                        Opportunity.expected_close_date.is_(None),
                        and_(
                            Opportunity.expected_close_date >= start_date.date(),
                            Opportunity.expected_close_date <= end_date.date(),
                        ),
                    ),
                )
                .group_by(Opportunity.stage)
                .all()
            )

            for stage_value, count, total_amount_raw in rows:
                stage = OpportunityStageEnum(stage_value)
                total_amount = float(total_amount_raw or 0)
                win_rate = self.STAGE_WIN_RATES.get(stage, 0.5)
                weighted_amount = total_amount * win_rate
                total_weighted += weighted_amount

                pipeline[stage.name] = {
                    "count": count,
                    "total_amount": total_amount,
                    "weighted_amount": weighted_amount,
                    "win_rate": win_rate * 100,
                }

            pipeline["total_weighted"] = total_weighted
            return pipeline

        except Exception as e:
            logger.error(f"漏斗分析失败：{e}")
            return {"total_weighted": 0.0}

    def _calculate_predicted_revenue(
        self,
        actual_revenue: float,
        pipeline_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """计算预测收入"""
        # 预测收入 = 已完成 + 漏斗加权金额 × 时间因子
        remaining_days = (end_date - datetime.now()).days
        total_days = max(1, (end_date - start_date).days)
        time_factor = min(1.0, max(0.0, remaining_days / total_days + 0.5))  # 至少 50% 的漏斗能转化

        weighted_pipeline = pipeline_data.get("total_weighted", 0)
        predicted_pipeline = weighted_pipeline * time_factor

        return actual_revenue + predicted_pipeline

    def _calculate_confidence_interval(
        self, predicted_revenue: float, pipeline_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算置信区间"""
        # 基于漏斗分布计算乐观/悲观场景
        total_weighted = pipeline_data.get("total_weighted", 0)

        # 乐观：高阶段商机全部转化
        optimistic = predicted_revenue + total_weighted * 0.2
        # 悲观：低阶段商机大部分流失
        pessimistic = predicted_revenue - total_weighted * 0.15

        return {
            "optimistic": round(optimistic, 2),
            "pessimistic": round(pessimistic, 2),
        }

    def _assess_risk(
        self,
        completion_rate: float,
        predicted_completion: float,
        pipeline_data: Dict[str, Any],
    ) -> str:
        """风险评估"""
        if predicted_completion < 80:
            return "HIGH"
        elif predicted_completion < 95:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_confidence_level(self, pipeline_data: Dict[str, Any]) -> int:
        """计算置信水平"""
        # 基于高阶段商机占比计算置信度
        total_weighted = pipeline_data.get("total_weighted", 0)
        if total_weighted == 0:
            return 50

        stage4_weighted = pipeline_data.get("NEGOTIATION", {}).get("weighted_amount", 0)
        stage5_weighted = pipeline_data.get("CLOSING", {}).get("weighted_amount", 0)

        high_stage_ratio = (stage4_weighted + stage5_weighted) / total_weighted

        # 高阶段占比越高，置信度越高
        confidence = 60 + int(high_stage_ratio * 40)  # 60-100
        return min(100, max(50, confidence))

    def _calculate_trend(self, historical: Dict[str, Any], predicted_completion: float) -> str:
        """计算趋势"""
        if not historical.get("last_quarter"):
            return "stable"

        last_completion = historical["last_quarter"].get("completion_rate", 100)
        if predicted_completion > last_completion + 5:
            return "up"
        elif predicted_completion < last_completion - 5:
            return "down"
        else:
            return "stable"

    def _get_historical_comparison(
        self, year: int, quarter: int, period: str
    ) -> Dict[str, Any]:
        """获取历史对比数据"""
        previous_year, previous_index = self._shift_period(year, quarter, period, -1)
        previous_start, previous_end = self._get_period_dates(previous_year, previous_index, period)
        previous_target = self._get_sales_target(previous_year, previous_index, period)
        previous_actual = self._get_actual_revenue(previous_start, previous_end)

        last_year_start, last_year_end = self._get_period_dates(year - 1, quarter, period)
        last_year_target = self._get_sales_target(year - 1, quarter, period)
        last_year_actual = self._get_actual_revenue(last_year_start, last_year_end)

        average_completion = self._get_average_same_period_completion(year, quarter, period)
        historical = {
            "last_quarter": {
                "period": self._format_period_label(previous_year, previous_index, period),
                "target": round(previous_target, 2),
                "actual": round(previous_actual, 2),
                "completion_rate": round(
                    previous_actual / previous_target * 100, 1
                ) if previous_target > 0 else 0.0,
            },
            "last_year_same_period": {
                "period": self._format_period_label(year - 1, quarter, period),
                "target": round(last_year_target, 2),
                "actual": round(last_year_actual, 2),
                "completion_rate": round(
                    last_year_actual / last_year_target * 100, 1
                ) if last_year_target > 0 else 0.0,
            },
            "average_same_period_completion": round(average_completion, 1),
        }

        if period == "quarterly":
            historical[f"average_q{quarter}_completion"] = round(average_completion, 1)
        elif period == "monthly":
            historical[f"average_m{quarter:02d}_completion"] = round(average_completion, 1)

        return historical

    def _shift_period(self, year: int, period_index: int, period: str, delta: int) -> tuple[int, int]:
        normalized_period = (period or "quarterly").lower()
        if normalized_period == "yearly":
            return year + delta, 1
        if normalized_period == "quarterly":
            total_quarters = year * 4 + (period_index - 1) + delta
            return total_quarters // 4, total_quarters % 4 + 1

        total_months = year * 12 + (period_index - 1) + delta
        return total_months // 12, total_months % 12 + 1

    def _get_average_same_period_completion(self, year: int, period_index: int, period: str) -> float:
        completions: List[float] = []
        for historical_year in range(year - 1, max(year - 4, 0), -1):
            start_date, end_date = self._get_period_dates(historical_year, period_index, period)
            target = self._get_sales_target(historical_year, period_index, period)
            if target <= 0:
                continue
            actual = self._get_actual_revenue(start_date, end_date)
            completions.append(actual / target * 100)

        if completions:
            return sum(completions) / len(completions)
        return 0.0

    @staticmethod
    def _format_period_label(year: int, period_index: int, period: str) -> str:
        normalized_period = (period or "quarterly").lower()
        if normalized_period == "yearly":
            return str(year)
        if normalized_period == "quarterly":
            return f"{year}-Q{period_index}"
        return f"{year}-{period_index:02d}"

    def _get_forecast_breakdown(
        self, actual_revenue: float, pipeline_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取预测分解"""
        # 已签约
        committed = {
            "amount": actual_revenue,
            "percentage": 0,
            "confidence": 100,
        }

        # 高概率（NEGOTIATION-CLOSING）
        best_case_amount = (
            pipeline_data.get("NEGOTIATION", {}).get("weighted_amount", 0)
            + pipeline_data.get("CLOSING", {}).get("weighted_amount", 0)
        )
        best_case = {
            "amount": best_case_amount,
            "percentage": 0,
            "confidence": 85,
        }

        # 漏斗中（DISCOVERY-PROPOSAL）
        pipeline_amount = (
            pipeline_data.get("DISCOVERY", {}).get("weighted_amount", 0)
            + pipeline_data.get("QUALIFICATION", {}).get("weighted_amount", 0)
            + pipeline_data.get("PROPOSAL", {}).get("weighted_amount", 0)
        )
        pipeline = {
            "amount": pipeline_amount,
            "percentage": 0,
            "confidence": 60,
        }

        # 计算百分比
        total = committed["amount"] + best_case["amount"] + pipeline["amount"]
        if total > 0:
            committed["percentage"] = round(committed["amount"] / total * 100, 1)
            best_case["percentage"] = round(best_case["amount"] / total * 100, 1)
            pipeline["percentage"] = round(pipeline["amount"] / total * 100, 1)

        return {
            "committed": committed,
            "best_case": best_case,
            "pipeline": pipeline,
        }

    def _identify_key_drivers(
        self,
        pipeline_data: Dict[str, Any],
        actual_revenue: float,
        target: float,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """识别关键驱动因素"""
        drivers = []
        signed_contracts = self._get_top_signed_contracts(start_date, end_date, limit=2)
        if signed_contracts:
            signed_total = sum(item["amount"] for item in signed_contracts)
            impact = round(signed_total / target * 100, 1) if target > 0 else 0.0
            contract_names = "、".join(item["name"] for item in signed_contracts)
            drivers.append(
                {
                    "factor": "大客户签约拉动",
                    "impact": min(20.0, max(3.0, impact)),
                    "description": (
                        f"{contract_names} 在本周期已签约，累计贡献 {round(signed_total, 2)} 元"
                    ),
                }
            )

        high_stage_opportunities = self._get_top_pipeline_opportunities(
            start_date,
            end_date,
            stages=[
                OpportunityStageEnum.NEGOTIATION.value,
                OpportunityStageEnum.CLOSING.value,
            ],
            limit=2,
        )
        if high_stage_opportunities:
            weighted_amount = round(
                sum(item["weighted_amount"] for item in high_stage_opportunities),
                2,
            )
            opportunity_names = "、".join(item["name"] for item in high_stage_opportunities)
            impact = round(weighted_amount / target * 100, 1) if target > 0 else 0.0
            drivers.append(
                {
                    "factor": "高阶段商机储备",
                    "impact": min(15.0, max(2.0, impact)),
                    "description": (
                        f"{opportunity_names} 处于高赢率阶段，加权贡献 {weighted_amount} 元"
                    ),
                }
            )

        # 季节性因素
        current_month = datetime.now().month
        if current_month in [1, 2]:
            drivers.append(
                {
                    "factor": "春节淡季影响",
                    "impact": -5,
                    "description": "春节假期导致有效工作日减少，商机推进和签约节奏偏慢",
                }
            )
        elif current_month in [3, 6, 9, 12]:
            drivers.append(
                {
                    "factor": "季度末冲刺窗口",
                    "impact": 8,
                    "description": "处于季度末冲刺窗口，高阶段商机更容易集中成交",
                }
            )

        if not drivers and actual_revenue > 0:
            completion_rate = round(actual_revenue / target * 100, 1) if target > 0 else 0.0
            drivers.append(
                {
                    "factor": "已签约收入沉淀",
                    "impact": completion_rate,
                    "description": f"当前周期已实现签约 {round(actual_revenue, 2)} 元",
                }
            )

        return drivers[:3]

    def _identify_risks(
        self,
        completion_rate: float,
        predicted_completion: float,
        pipeline_data: Dict[str, Any],
        target: float,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """识别风险"""
        risks = []

        # 完成率低
        if completion_rate < 50:
                risks.append({
                    "risk": "当前完成率偏低",
                    "impact": -max(5_000_000, round(target * 0.1, 2)),
                    "probability": "HIGH",
                    "mitigation": "加速商机推进，争取季度末签约",
                })

        overdue_opportunities = self._get_overdue_opportunities(start_date, end_date, limit=2)
        if overdue_opportunities:
            overdue_weighted = round(
                sum(item["weighted_amount"] for item in overdue_opportunities),
                2,
            )
            opportunity_names = "、".join(item["name"] for item in overdue_opportunities)
            risks.append(
                {
                    "risk": "高价值商机预计成交已逾期",
                    "impact": -overdue_weighted,
                    "probability": "HIGH" if overdue_weighted >= 2_000_000 else "MEDIUM",
                    "mitigation": f"优先复盘并重新推进 {opportunity_names}",
                }
            )

        # 漏斗中高阶段占比低
        total_weighted = pipeline_data.get("total_weighted", 0)
        if total_weighted > 0:
            stage4_5_ratio = (
                pipeline_data.get("NEGOTIATION", {}).get("weighted_amount", 0)
                + pipeline_data.get("CLOSING", {}).get("weighted_amount", 0)
            ) / total_weighted

            if stage4_5_ratio < 0.3:
                risks.append({
                    "risk": "高阶段商机不足",
                    "impact": -round(max(3_000_000, total_weighted * 0.25), 2),
                    "probability": "MEDIUM",
                    "mitigation": "加强商机培育，加速推进",
                })

        return risks[:3]

    def _generate_recommendations(
        self,
        pipeline_data: Dict[str, Any],
        risk_level: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """生成建议行动"""
        recommendations = []
        priority = 1

        # 根据风险等级生成建议
        if risk_level in ["HIGH", "MEDIUM"]:
            for opportunity in self._get_top_pipeline_opportunities(
                start_date,
                end_date,
                stages=[
                    OpportunityStageEnum.NEGOTIATION.value,
                    OpportunityStageEnum.CLOSING.value,
                ],
                limit=2,
            ):
                recommendations.append(
                    {
                        "priority": priority,
                        "action": f"重点跟进 {opportunity['name']}",
                        "impact": round(opportunity["weighted_amount"], 2),
                        "deadline": self._format_close_deadline(opportunity["expected_close_date"]),
                    }
                )
                priority += 1

            if not recommendations:
                recommendations.append(
                    {
                        "priority": priority,
                        "action": "重点跟进高阶段商机",
                        "impact": 3_000_000,
                        "deadline": self._format_deadline(
                            min(datetime.now().date() + timedelta(days=7), end_date.date())
                        ),
                    }
                )
                priority += 1

            early_stage_opportunities = self._get_top_pipeline_opportunities(
                start_date,
                end_date,
                stages=[
                    OpportunityStageEnum.QUALIFICATION.value,
                    OpportunityStageEnum.PROPOSAL.value,
                ],
                limit=3,
            )
            if early_stage_opportunities:
                recommendations.append(
                    {
                        "priority": priority,
                        "action": "加速中前期商机转化",
                        "impact": round(
                            sum(item["weighted_amount"] for item in early_stage_opportunities),
                            2,
                        ),
                        "deadline": self._format_deadline(
                            min(datetime.now().date() + timedelta(days=10), end_date.date())
                        ),
                    }
                )
                priority += 1

        # 季度末冲刺建议
        current_month = datetime.now().month
        if current_month in [3, 6, 9, 12] and datetime.now().day > 15:
            recommendations.append(
                {
                    "priority": priority,
                    "action": "启动季度末冲刺激励",
                    "impact": 1_500_000,
                    "deadline": self._format_deadline(end_date.date()),
                }
            )

        return recommendations[:3]

    def _get_top_signed_contracts(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Contract.contract_name,
                Customer.customer_name,
                Contract.total_amount,
            )
            .join(Customer, Customer.id == Contract.customer_id)
            .filter(
                Contract.signing_date.isnot(None),
                Contract.signing_date >= start_date.date(),
                Contract.signing_date <= end_date.date(),
                Contract.status.in_(self.VALID_CONTRACT_STATUSES),
                Contract.total_amount.isnot(None),
            )
            .order_by(Contract.total_amount.desc(), Contract.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "name": contract_name or customer_name or "未命名合同",
                "customer_name": customer_name or "未命名客户",
                "amount": float(total_amount or 0),
            }
            for contract_name, customer_name, total_amount in rows
        ]

    def _get_top_pipeline_opportunities(
        self,
        start_date: datetime,
        end_date: datetime,
        stages: Optional[List[str]] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        selected_stages = stages or list(self.ACTIVE_PIPELINE_STAGES)
        rows = (
            self.db.query(
                Opportunity.opp_name,
                Customer.customer_name,
                Opportunity.stage,
                Opportunity.est_amount,
                Opportunity.expected_close_date,
            )
            .join(Customer, Customer.id == Opportunity.customer_id)
            .filter(
                Opportunity.stage.in_(selected_stages),
                Opportunity.est_amount.isnot(None),
                or_(
                    Opportunity.expected_close_date.is_(None),
                    and_(
                        Opportunity.expected_close_date >= start_date.date(),
                        Opportunity.expected_close_date <= end_date.date(),
                    ),
                ),
            )
            .all()
        )
        opportunities = []
        for opp_name, customer_name, stage, est_amount, expected_close_date in rows:
            stage_enum = OpportunityStageEnum(stage)
            weighted_amount = float(est_amount or 0) * self.STAGE_WIN_RATES.get(stage_enum, 0.5)
            opportunities.append(
                {
                    "name": opp_name or customer_name or "未命名商机",
                    "customer_name": customer_name or "未命名客户",
                    "stage": stage,
                    "amount": float(est_amount or 0),
                    "weighted_amount": weighted_amount,
                    "expected_close_date": expected_close_date,
                }
            )
        opportunities.sort(key=lambda item: item["weighted_amount"], reverse=True)
        return opportunities[:limit]

    def _get_overdue_opportunities(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(
                Opportunity.opp_name,
                Customer.customer_name,
                Opportunity.stage,
                Opportunity.est_amount,
                Opportunity.expected_close_date,
            )
            .join(Customer, Customer.id == Opportunity.customer_id)
            .filter(
                Opportunity.stage.in_(self.ACTIVE_PIPELINE_STAGES),
                Opportunity.est_amount.isnot(None),
                Opportunity.expected_close_date.isnot(None),
                Opportunity.expected_close_date >= start_date.date(),
                Opportunity.expected_close_date <= end_date.date(),
                Opportunity.expected_close_date < date.today(),
            )
            .all()
        )
        opportunities = []
        for opp_name, customer_name, stage, est_amount, expected_close_date in rows:
            stage_enum = OpportunityStageEnum(stage)
            weighted_amount = float(est_amount or 0) * self.STAGE_WIN_RATES.get(stage_enum, 0.5)
            opportunities.append(
                {
                    "name": opp_name or customer_name or "未命名商机",
                    "customer_name": customer_name or "未命名客户",
                    "stage": stage,
                    "amount": float(est_amount or 0),
                    "weighted_amount": weighted_amount,
                    "expected_close_date": expected_close_date,
                }
            )
        opportunities.sort(key=lambda item: item["weighted_amount"], reverse=True)
        return opportunities[:limit]

    def _format_deadline(self, deadline: date) -> str:
        return f"{deadline.month} 月 {deadline.day} 日前"

    def _format_close_deadline(self, deadline: Optional[date]) -> str:
        if deadline is None:
            return "本周期内"
        return self._format_deadline(deadline)


__all__ = ["SalesForecastService"]
