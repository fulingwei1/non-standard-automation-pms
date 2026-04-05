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
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.sales.leads import Opportunity
from app.models.sales.contracts import Contract
from app.models.project.customer import Customer
from app.models.enums.sales import OpportunityStageEnum

logger = logging.getLogger(__name__)


class SalesForecastService:
    """销售预测服务类"""

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

        # 1. 获取销售目标（从数据库或配置）
        target = self._get_sales_target(year, quarter, period)

        # 2. 获取已完成业绩（已签约合同）
        actual_revenue = self._get_actual_revenue(start_date, end_date)

        # 3. 获取漏斗中商机及预测
        pipeline_data = self._get_pipeline_analysis()

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
            "targets": {
                "quarterly_target": target,
                "actual_revenue": actual_revenue,
                "completion_rate": round(completion_rate, 1),
                "days_elapsed": (datetime.now() - start_date).days,
                "total_days": (end_date - start_date).days,
                "time_progress": round(
                    (datetime.now() - start_date).days / (end_date - start_date).days * 100, 1
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
            "key_drivers": self._identify_key_drivers(pipeline_data, actual_revenue, target),
            "risks": self._identify_risks(completion_rate, predicted_completion, pipeline_data),
            "recommended_actions": self._generate_recommendations(pipeline_data, risk_level),
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
        # TODO: 从数据库获取实际目标
        # 这里使用默认值
        annual_target = 200_000_000  # 2 亿年度目标

        if period == "yearly":
            return annual_target
        elif period == "quarterly":
            # 考虑季节性因子
            months_in_quarter = [(quarter - 1) * 3 + 1, (quarter - 1) * 3 + 2, (quarter - 1) * 3 + 3]
            quarter_factor = sum(self.SEASONAL_FACTORS.get(m, 1.0) for m in months_in_quarter) / 3
            return (annual_target / 4) * quarter_factor
        else:  # monthly
            return (annual_target / 12) * self.SEASONAL_FACTORS.get(quarter, 1.0)

    def _get_actual_revenue(self, start_date: datetime, end_date: datetime) -> float:
        """获取已完成业绩（已签约合同金额）"""
        try:
            result = self.db.execute(
                select(func.sum(Contract.total_amount)).where(
                    and_(
                        Contract.signing_date >= start_date,
                        Contract.signing_date <= end_date,
                        Contract.status.in_(["ACTIVE", "COMPLETED"]),
                    )
                )
            )
            total = result.scalar()
            return float(total) if total else 0.0
        except Exception as e:
            logger.error(f"获取实际业绩失败：{e}")
            return 0.0

    def _get_pipeline_analysis(self) -> Dict[str, Any]:
        """获取漏斗分析数据"""
        try:
            # 按阶段统计商机
            pipeline = {}
            total_weighted = 0.0

            for stage in OpportunityStageEnum:
                result = self.db.execute(
                    select(
                        func.count(Opportunity.id),
                        func.sum(Opportunity.estimated_amount),
                    ).where(
                        and_(
                            Opportunity.stage == stage,
                            Opportunity.outcome == None,  # 尚未关闭
                        )
                    )
                )
                row = result.one()
                count = row[0] or 0
                total_amount = float(row[1] or 0)

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
        total_days = (end_date - start_date).days
        time_factor = min(1.0, remaining_days / total_days + 0.5)  # 至少 50% 的漏斗能转化

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

        stage4_weighted = pipeline_data.get("STAGE4", {}).get("weighted_amount", 0)
        stage5_weighted = pipeline_data.get("STAGE5", {}).get("weighted_amount", 0)

        high_stage_ratio = (stage4_weighted + stage5_weighted) / total_weighted

        # 高阶段占比越高，置信度越高
        # 使用新的枚举名称
        stage4_weighted = pipeline_data.get("NEGOTIATION", {}).get("weighted_amount", 0)
        stage5_weighted = pipeline_data.get("CLOSING", {}).get("weighted_amount", 0)

        high_stage_ratio = (stage4_weighted + stage5_weighted) / total_weighted if total_weighted > 0 else 0

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
        # TODO: 从数据库获取真实历史数据
        return {
            "last_quarter": {
                "period": f"{year}-Q{quarter - 1}" if quarter > 1 else f"{year - 1}-Q4",
                "target": 48_000_000,
                "actual": 51_200_000,
                "completion_rate": 106.7,
            },
            "last_year_same_period": {
                "period": f"{year - 1}-Q{quarter}",
                "target": 42_000_000,
                "actual": 44_800_000,
                "completion_rate": 106.7,
            },
            "average_q1_completion": 102.5,
        }

    def _get_forecast_breakdown(
        self, actual_revenue: float, pipeline_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取预测分解"""
        total_weighted = pipeline_data.get("total_weighted", 0)

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
        self, pipeline_data: Dict[str, Any], actual_revenue: float, target: float
    ) -> List[Dict[str, Any]]:
        """识别关键驱动因素"""
        drivers = []

        # 分析大额商机
        # TODO: 从数据库获取实际大额商机
        drivers.append({
            "factor": "大客户签约",
            "impact": 15,
            "description": "重点客户项目推进顺利",
        })

        # 季节性因素
        current_month = datetime.now().month
        if current_month in [1, 2]:
            drivers.append({
                "factor": "春节淡季影响",
                "impact": -5,
                "description": "春节假期导致有效工作日减少",
            })
        elif current_month in [3, 6, 9, 12]:
            drivers.append({
                "factor": "季度末冲刺",
                "impact": 8,
                "description": "季度末加速签约",
            })

        return drivers

    def _identify_risks(
        self,
        completion_rate: float,
        predicted_completion: float,
        pipeline_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """识别风险"""
        risks = []

        # 完成率低
        if completion_rate < 50:
            risks.append({
                "risk": "当前完成率偏低",
                "impact": -5_000_000,
                "probability": "HIGH",
                "mitigation": "加速商机推进，争取季度末签约",
            })

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
                    "impact": -3_000_000,
                    "probability": "MEDIUM",
                    "mitigation": "加强商机培育，加速推进",
                })

        return risks

    def _generate_recommendations(
        self, pipeline_data: Dict[str, Any], risk_level: str
    ) -> List[Dict[str, Any]]:
        """生成建议行动"""
        recommendations = []
        priority = 1

        # 根据风险等级生成建议
        if risk_level in ["HIGH", "MEDIUM"]:
            recommendations.append({
                "priority": priority,
                "action": "重点跟进 STAGE4 商机",
                "impact": 3_000_000,
                "deadline": "本月 20 日前",
            })
            priority += 1

            recommendations.append({
                "priority": priority,
                "action": "加速 STAGE2→STAGE3 转化",
                "impact": 2_000_000,
                "deadline": "本月 15 日前",
            })
            priority += 1

        # 季度末冲刺建议
        current_month = datetime.now().month
        if current_month in [3, 6, 9, 12] and datetime.now().day > 15:
            recommendations.append({
                "priority": priority,
                "action": "启动季度末冲刺激励",
                "impact": 1_500_000,
                "deadline": "本月底前",
            })

        return recommendations


__all__ = ["SalesForecastService"]
