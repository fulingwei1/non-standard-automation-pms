# -*- coding: utf-8 -*-
"""
销售预测服务
实现基于历史数据的预测模型：移动平均法、指数平滑法、商机赢单概率预测、收入预测
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.project import Customer
from app.models.sales import Contract, Lead, Opportunity, Quote


class SalesPredictionService:
    """销售预测服务"""

    # 可配置的预测参数（可通过构造函数覆盖或后续迁移到数据库/配置文件）
    DEFAULT_STAGE_WEIGHTS = {
        "PROPOSAL": 0.6,
        "NEGOTIATION": 0.8,
    }
    DEFAULT_STAGE_WIN_RATES = {
        "DISCOVERY": 0.1,
        "QUALIFIED": 0.3,
        "PROPOSAL": 0.5,
        "NEGOTIATION": 0.7,
        "WON": 1.0,
        "LOST": 0.0,
    }
    DEFAULT_AMOUNT_FACTORS = {
        "large": {"threshold": 1000000, "factor": 0.9},      # >100万
        "medium": {"threshold": 500000, "factor": 0.95},      # >50万
        "small": {"threshold": 100000, "factor": 1.1},        # <10万（反向）
    }
    DEFAULT_SMOOTHING_ALPHA = 0.3
    DEFAULT_WIN_RATE_FALLBACK = 0.5
    DEFAULT_PROBABILITY_BOUNDS = (0.1, 0.95)

    def __init__(self, db: Session, **config):
        self.db = db
        self.stage_weights = config.get("stage_weights", self.DEFAULT_STAGE_WEIGHTS)
        self.stage_win_rates = config.get("stage_win_rates", self.DEFAULT_STAGE_WIN_RATES)
        self.amount_factors = config.get("amount_factors", self.DEFAULT_AMOUNT_FACTORS)
        self.smoothing_alpha = config.get("smoothing_alpha", self.DEFAULT_SMOOTHING_ALPHA)
        self.win_rate_fallback = config.get("win_rate_fallback", self.DEFAULT_WIN_RATE_FALLBACK)
        self.probability_bounds = config.get("probability_bounds", self.DEFAULT_PROBABILITY_BOUNDS)

    def predict_revenue(
        self,
        *,
        days: int = 90,
        method: str = "moving_average",
        customer_id: Optional[int] = None,
        owner_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        收入预测模型
        支持未来 30/60/90 天收入预测

        Args:
            days: 预测天数（30/60/90）
            method: 预测方法（moving_average/exponential_smoothing）
            customer_id: 客户ID筛选（可选）
            owner_id: 负责人ID筛选（可选）
        """
        today = date.today()

        # 获取历史合同数据（用于训练预测模型）
        query_contracts = self.db.query(Contract).filter(
            Contract.status == "SIGNED",
            Contract.contract_amount.isnot(None),
        )

        if customer_id:
            query_contracts = query_contracts.filter(Contract.customer_id == customer_id)
        if owner_id:
            query_contracts = query_contracts.filter(Contract.owner_id == owner_id)

        contracts = query_contracts.order_by(Contract.signed_date.desc()).limit(100).all()

        # 获取历史月度收入数据
        monthly_revenue = self._get_monthly_revenue(contracts)

        # 获取进行中的商机（用于预测）
        query_opps = self.db.query(Opportunity).filter(
            Opportunity.stage.in_(["PROPOSAL", "NEGOTIATION"]),
            Opportunity.est_amount.isnot(None),
        )

        if customer_id:
            query_opps = query_opps.join(Customer).filter(Customer.id == customer_id)
        if owner_id:
            query_opps = query_opps.filter(Opportunity.owner_id == owner_id)

        opportunities = query_opps.all()

        # 计算预测值
        if method == "moving_average":
            predicted_revenue = self._moving_average_forecast(monthly_revenue, days)
        elif method == "exponential_smoothing":
            predicted_revenue = self._exponential_smoothing_forecast(monthly_revenue, days)
        else:
            predicted_revenue = self._moving_average_forecast(monthly_revenue, days)

        # 基于商机的收入预测
        opportunity_based_revenue = self._forecast_from_opportunities(opportunities, days)

        # 合并预测结果
        final_forecast = {
            "method": method,
            "days": days,
            "predicted_revenue": float(predicted_revenue),
            "opportunity_based_revenue": float(opportunity_based_revenue),
            "combined_revenue": float((predicted_revenue + opportunity_based_revenue) / 2),
            "confidence_level": self._calculate_confidence(monthly_revenue, len(opportunities)),
            "breakdown": self._generate_breakdown(days, predicted_revenue, opportunity_based_revenue),
        }

        return final_forecast

    def predict_win_probability(
        self,
        *,
        opportunity_id: Optional[int] = None,
        stage: Optional[str] = None,
        amount: Optional[Decimal] = None,
        customer_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        商机赢单概率预测
        基于商机阶段、金额、历史赢单率

        Args:
            opportunity_id: 商机ID（如果提供，会获取实际商机数据）
            stage: 商机阶段
            amount: 商机金额
            customer_id: 客户ID
        """
        # 如果提供了商机ID，获取实际数据
        if opportunity_id:
            opp = self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
            if opp:
                stage = opp.stage
                amount = opp.est_amount
                customer_id = opp.customer_id

        if not stage:
            return {"win_probability": 0.5, "confidence": "LOW", "factors": []}

        # 获取历史赢单率数据
        historical_win_rate = self._get_historical_win_rate_by_stage()
        customer_win_rate = self._get_customer_win_rate(customer_id) if customer_id else None

        # 计算基础赢单概率
        base_probability = historical_win_rate.get(stage, self.win_rate_fallback)

        # 根据金额调整（大单通常赢单率较低）
        amount_factor = 1.0
        if amount:
            large = self.amount_factors["large"]
            medium = self.amount_factors["medium"]
            small = self.amount_factors["small"]
            if amount > Decimal(str(large["threshold"])):
                amount_factor = large["factor"]
            elif amount > Decimal(str(medium["threshold"])):
                amount_factor = medium["factor"]
            elif amount < Decimal(str(small["threshold"])):
                amount_factor = small["factor"]

        # 根据客户历史赢单率调整
        customer_factor = 1.0
        if customer_win_rate:
            customer_factor = customer_win_rate

        # 计算最终概率
        final_probability = base_probability * amount_factor * customer_factor
        lo, hi = self.probability_bounds
        final_probability = max(lo, min(hi, final_probability))

        # 计算置信度
        confidence = "HIGH" if len(historical_win_rate) > 10 else "MEDIUM" if len(historical_win_rate) > 5 else "LOW"

        factors = [
            {"factor": "阶段", "value": stage, "impact": f"{base_probability:.1%}"},
            {"factor": "金额", "value": f"¥{float(amount or 0):,.0f}" if amount else "未知", "impact": f"{amount_factor:.1%}"},
        ]
        if customer_win_rate:
            factors.append({"factor": "客户历史", "value": f"{customer_win_rate:.1%}", "impact": f"{customer_factor:.1%}"})

        return {
            "win_probability": float(final_probability),
            "confidence": confidence,
            "factors": factors,
            "base_probability": float(base_probability),
            "amount_factor": float(amount_factor),
            "customer_factor": float(customer_factor),
        }

    def _get_monthly_revenue(self, contracts: List[Contract]) -> List[Dict[str, Any]]:
        """获取历史月度收入数据"""
        monthly_data = defaultdict(lambda: {"count": 0, "amount": Decimal("0")})

        for contract in contracts:
            if contract.signed_date:
                month_key = contract.signed_date.strftime("%Y-%m")
                monthly_data[month_key]["count"] += 1
                monthly_data[month_key]["amount"] += contract.contract_amount or Decimal("0")

        # 转换为列表并按月份排序
        result = []
        for month in sorted(monthly_data.keys()):
            result.append({
                "month": month,
                "revenue": float(monthly_data[month]["amount"]),
                "count": monthly_data[month]["count"],
            })

        return result

    def _moving_average_forecast(self, monthly_data: List[Dict[str, Any]], days: int) -> Decimal:
        """移动平均法预测"""
        if not monthly_data:
            return Decimal("0")

        # 使用最近3个月的平均值
        recent_months = monthly_data[-3:] if len(monthly_data) >= 3 else monthly_data
        avg_revenue = sum([m["revenue"] for m in recent_months]) / len(recent_months)

        # 按天数比例计算
        months = days / 30.0
        return Decimal(str(avg_revenue * months))

    def _exponential_smoothing_forecast(self, monthly_data: List[Dict[str, Any]], days: int, alpha: float = None) -> Decimal:
        """指数平滑法预测"""
        if not monthly_data:
            return Decimal("0")

        if alpha is None:
            alpha = self.smoothing_alpha

        # 简单指数平滑
        revenues = [m["revenue"] for m in monthly_data]
        if len(revenues) == 1:
            forecast = revenues[0]
        else:
            # 初始值使用第一个数据点
            forecast = revenues[0]
            for revenue in revenues[1:]:
                forecast = alpha * revenue + (1 - alpha) * forecast

        # 按天数比例计算
        months = days / 30.0
        return Decimal(str(forecast * months))

    def _forecast_from_opportunities(self, opportunities: List[Opportunity], days: int) -> Decimal:
        """基于商机的收入预测"""
        if not opportunities:
            return Decimal("0")

        # 根据商机阶段和预计签约时间估算
        total_amount = Decimal("0")
        for opp in opportunities:
            est_amount = opp.est_amount or Decimal("0")

            # 根据阶段调整概率（使用可配置权重）
            weight = self.stage_weights.get(opp.stage, self.win_rate_fallback)

            total_amount += est_amount * Decimal(str(weight))

        # 假设这些商机在未来 days 天内平均分布
        # 简化处理：假设在接下来3个月内平均分布
        months = days / 30.0
        return total_amount * Decimal(str(min(months / 3.0, 1.0)))

    def _get_historical_win_rate_by_stage(self) -> Dict[str, float]:
        """获取各阶段的历史赢单率"""
        # 统计各阶段的商机数量和赢单数量
        stage_stats = defaultdict(lambda: {"total": 0, "won": 0})

        opportunities = self.db.query(Opportunity).filter(
            Opportunity.stage.in_(["DISCOVERY", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "WON", "LOST"])
        ).all()

        for opp in opportunities:
            stage = opp.stage
            stage_stats[stage]["total"] += 1
            if stage == "WON":
                stage_stats[stage]["won"] += 1

        # 计算赢单率（对于非WON阶段，计算从该阶段到WON的转化率）
        win_rates = {}
        total_won = stage_stats["WON"]["total"]
        total_lost = stage_stats["LOST"]["total"]
        total_closed = total_won + total_lost

        if total_closed > 0:
            overall_win_rate = total_won / total_closed
        else:
            overall_win_rate = self.win_rate_fallback

        # 为各阶段分配赢单率（基于可配置的阶段权重）
        for stage, weight in self.stage_win_rates.items():
            if stage in ["WON", "LOST"]:
                win_rates[stage] = weight
            else:
                # 基于历史数据和阶段权重计算
                stage_total = stage_stats[stage]["total"]
                if stage_total > 0:
                    # 使用阶段权重和历史转化率结合
                    win_rates[stage] = weight * overall_win_rate
                else:
                    win_rates[stage] = weight * self.win_rate_fallback

        return win_rates

    def _get_customer_win_rate(self, customer_id: int) -> Optional[float]:
        """获取客户的历史赢单率"""
        if not customer_id:
            return None

        # 统计该客户的商机
        opportunities = self.db.query(Opportunity).filter(
            Opportunity.customer_id == customer_id,
            Opportunity.stage.in_(["WON", "LOST"])
        ).all()

        if not opportunities:
            return None

        won_count = len([opp for opp in opportunities if opp.stage == "WON"])
        total_count = len(opportunities)

        return won_count / total_count if total_count > 0 else None

    def _calculate_confidence(self, monthly_data: List[Dict[str, Any]], opportunity_count: int) -> str:
        """计算预测置信度"""
        data_points = len(monthly_data)

        if data_points >= 6 and opportunity_count >= 5:
            return "HIGH"
        elif data_points >= 3 and opportunity_count >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_breakdown(self, days: int, predicted_revenue: Decimal, opportunity_revenue: Decimal) -> List[Dict[str, Any]]:
        """生成预测明细（按时间段）"""
        breakdown = []
        periods = [30, 60, 90] if days >= 90 else ([30, 60] if days >= 60 else [30])

        for period in periods:
            if period > days:
                continue

            ratio = period / days
            breakdown.append({
                "period": period,
                "period_label": f"未来{period}天",
                "predicted_revenue": float(predicted_revenue * Decimal(str(ratio))),
                "opportunity_revenue": float(opportunity_revenue * Decimal(str(ratio))),
                "combined_revenue": float((predicted_revenue + opportunity_revenue) / 2 * Decimal(str(ratio))),
            })

        return breakdown

    def evaluate_prediction_accuracy(self, days_back: int = 90) -> Dict[str, Any]:
        """
        评估预测准确度
        对比历史预测值和实际值
        """
        # 这里简化实现，实际应该存储历史预测值
        # 当前实现：基于历史数据的统计

        today = date.today()
        start_date = today - timedelta(days=days_back)

        # 获取该时间段内实际签约的合同
        actual_contracts = self.db.query(Contract).filter(
            Contract.status == "SIGNED",
            Contract.signed_date >= start_date,
            Contract.signed_date <= today,
        ).all()

        actual_revenue = sum([float(c.contract_amount or 0) for c in actual_contracts])

        # 获取该时间段开始时的商机（模拟历史预测）
        historical_opps = self.db.query(Opportunity).filter(
            Opportunity.created_at <= start_date,
            Opportunity.stage.in_(["PROPOSAL", "NEGOTIATION"]),
        ).all()

        # 计算预测值（基于历史商机）
        predicted_revenue = self._forecast_from_opportunities(historical_opps, days_back)

        # 计算准确度
        if actual_revenue > 0:
            accuracy = min(1.0, float(predicted_revenue) / actual_revenue) if predicted_revenue > 0 else 0.0
            error_rate = abs(1.0 - accuracy)
        else:
            accuracy = 0.0
            error_rate = 1.0

        return {
            "period": f"过去{days_back}天",
            "actual_revenue": actual_revenue,
            "predicted_revenue": float(predicted_revenue),
            "accuracy": accuracy,
            "error_rate": error_rate,
            "mape": error_rate * 100,  # Mean Absolute Percentage Error
        }
