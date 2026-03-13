"""
AI智能成本估算服务

通过委托子模块实现职责分离：
- 成本计算：cost.cost_calculator
- 优化建议：cost.optimization_engine
- 定价推荐：cost.pricing_engine
- 置信度评分：cost.confidence_scorer
- 历史分析：cost.historical_analyzer
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.sales.presale_ai_cost import PresaleAICostEstimation
from app.schemas.sales.presale_ai_cost import (
    CostBreakdown,
    CostEstimationInput,
    CostEstimationResponse,
    CostOptimizationInput,
    CostOptimizationResponse,
    HistoricalAccuracyResponse,
    OptimizationSuggestion,
    PricingInput,
    PricingResponse,
    UpdateActualCostInput,
)
from app.services.sales.cost.confidence_scorer import ConfidenceScorer
from app.services.sales.cost.cost_calculator import CostCalculator
from app.services.sales.cost.historical_analyzer import HistoricalAnalyzer
from app.services.sales.cost.optimization_engine import OptimizationEngine
from app.services.sales.cost.pricing_engine import PricingEngine
from app.utils.db_helpers import save_obj
from app.utils.decimal_helpers import ZERO


class AICostEstimationService:
    """
    AI成本估算服务

    提供智能化的成本估算、优化建议和定价推荐功能。
    通过组合多个专业引擎实现职责分离和可维护性。
    """

    MODEL_VERSION = "v1.0.0"

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        # 初始化子模块
        self._calculator = CostCalculator(db)
        self._optimizer = OptimizationEngine()
        self._pricer = PricingEngine()
        self._scorer = ConfidenceScorer(db)
        self._historian = HistoricalAnalyzer(db)

    async def estimate_cost(self, input_data: CostEstimationInput) -> CostEstimationResponse:
        """
        智能成本估算

        整合各子模块能力，完成完整的成本估算流程：
        1. 计算各项成本
        2. 生成优化建议
        3. 生成定价推荐
        4. 评估置信度
        5. 保存估算结果

        Args:
            input_data: 估算输入数据

        Returns:
            完整的成本估算响应
        """
        # 1. 计算各项成本（委托给 CostCalculator）
        hardware_cost = self._calculator.calculate_hardware_cost(input_data.hardware_items)
        software_cost = self._calculator.calculate_software_cost(
            input_data.software_requirements, input_data.estimated_man_days
        )
        installation_cost = self._calculator.calculate_installation_cost(
            input_data.installation_difficulty, hardware_cost
        )
        service_cost = self._calculator.calculate_service_cost(
            hardware_cost + software_cost, input_data.service_years or 1
        )
        risk_reserve = self._calculator.calculate_risk_reserve(
            input_data.project_type,
            input_data.complexity_level,
            hardware_cost + software_cost + installation_cost,
        )

        total_cost = hardware_cost + software_cost + installation_cost + service_cost + risk_reserve

        # 构建成本明细
        cost_breakdown = {
            "hardware_cost": hardware_cost,
            "software_cost": software_cost,
            "installation_cost": installation_cost,
            "service_cost": service_cost,
            "risk_reserve": risk_reserve,
        }

        # 2. 生成优化建议（委托给 OptimizationEngine）
        optimization_suggestions = await self._optimizer.generate_suggestions(
            input_data, cost_breakdown
        )

        # 3. 生成定价推荐（委托给 PricingEngine）
        target_margin = input_data.target_margin_rate or Decimal("0.30")
        pricing_recommendations = self._pricer.generate_recommendations(total_cost, target_margin)

        # 4. 计算置信度（委托给 ConfidenceScorer）
        confidence_score = self._scorer.calculate_score(input_data)

        # 5. 保存到数据库
        estimation = PresaleAICostEstimation(
            presale_ticket_id=input_data.presale_ticket_id,
            solution_id=input_data.solution_id,
            hardware_cost=hardware_cost,
            software_cost=software_cost,
            installation_cost=installation_cost,
            service_cost=service_cost,
            risk_reserve=risk_reserve,
            total_cost=total_cost,
            optimization_suggestions=[s.dict() for s in optimization_suggestions],
            pricing_recommendations=pricing_recommendations.dict(),
            confidence_score=confidence_score,
            model_version=self.MODEL_VERSION,
            input_parameters=input_data.dict(),
            created_by=self.user_id,
        )

        save_obj(self.db, estimation)

        # 6. 构建响应
        return CostEstimationResponse(
            id=estimation.id,
            presale_ticket_id=estimation.presale_ticket_id,
            solution_id=estimation.solution_id,
            cost_breakdown=CostBreakdown(
                hardware_cost=hardware_cost,
                software_cost=software_cost,
                installation_cost=installation_cost,
                service_cost=service_cost,
                risk_reserve=risk_reserve,
                total_cost=total_cost,
            ),
            optimization_suggestions=optimization_suggestions,
            pricing_recommendations=pricing_recommendations,
            confidence_score=confidence_score,
            model_version=self.MODEL_VERSION,
            created_at=estimation.created_at,
        )

    async def optimize_cost(self, input_data: CostOptimizationInput) -> CostOptimizationResponse:
        """
        成本优化分析

        基于已有估算结果，筛选可行的优化建议。

        Args:
            input_data: 优化输入（包含估算ID和风险偏好）

        Returns:
            优化后的成本和建议列表
        """
        estimation = (
            self.db.query(PresaleAICostEstimation)
            .filter(PresaleAICostEstimation.id == input_data.estimation_id)
            .first()
        )

        if not estimation:
            raise ValueError(f"估算记录不存在: {input_data.estimation_id}")

        # 应用优化建议
        original_total = estimation.total_cost
        optimized_total = original_total

        suggestions = []
        if estimation.optimization_suggestions:
            for sug_dict in estimation.optimization_suggestions:
                sug = OptimizationSuggestion(**sug_dict)

                # 根据风险接受度过滤（委托给 OptimizationEngine）
                if self._optimizer.is_acceptable_risk(sug, input_data.max_risk_level):
                    suggestions.append(sug)
                    optimized_total -= sug.saving_amount

        total_saving = original_total - optimized_total
        total_saving_rate = (
            (total_saving / original_total * Decimal("100")) if original_total > 0 else ZERO
        )

        avg_feasibility = self._optimizer.calculate_avg_feasibility(suggestions)

        return CostOptimizationResponse(
            original_total_cost=original_total,
            optimized_total_cost=optimized_total,
            total_saving=total_saving,
            total_saving_rate=total_saving_rate,
            suggestions=suggestions,
            feasibility_summary=f"共有{len(suggestions)}项优化建议,总体可行性评分: {avg_feasibility:.2f}",
        )

    async def recommend_pricing(self, input_data: PricingInput) -> PricingResponse:
        """
        定价推荐

        基于成本和市场因素生成定价建议。

        Args:
            input_data: 定价输入（包含估算ID、目标利润率、市场竞争等）

        Returns:
            定价推荐和敏感度分析
        """
        estimation = (
            self.db.query(PresaleAICostEstimation)
            .filter(PresaleAICostEstimation.id == input_data.estimation_id)
            .first()
        )

        if not estimation:
            raise ValueError(f"估算记录不存在: {input_data.estimation_id}")

        # 生成基础定价（委托给 PricingEngine）
        base_pricing = self._pricer.generate_recommendations(
            estimation.total_cost, input_data.target_margin_rate
        )

        # 根据市场竞争调整
        adjusted_pricing = self._pricer.adjust_for_competition(
            base_pricing, input_data.market_competition_level
        )

        # 价格敏感度分析
        sensitivity_analysis = self._pricer.analyze_sensitivity(
            estimation.total_cost, adjusted_pricing, input_data.customer_budget
        )

        # 计算竞争力评分
        competitiveness = self._pricer.calculate_competitiveness(
            adjusted_pricing, input_data.customer_budget
        )

        return PricingResponse(
            cost_base=estimation.total_cost,
            pricing_recommendations=adjusted_pricing,
            sensitivity_analysis=sensitivity_analysis,
            competitiveness_score=competitiveness,
        )

    async def get_historical_accuracy(self) -> HistoricalAccuracyResponse:
        """
        获取历史预测准确度

        分析历史估算的准确性，用于模型评估和改进。

        Returns:
            历史准确度统计
        """
        return await self._historian.get_accuracy()

    async def update_actual_cost(self, input_data: UpdateActualCostInput) -> Dict[str, Any]:
        """
        更新实际成本（用于学习）

        记录项目实际成本，用于模型学习和准确度提升。

        Args:
            input_data: 实际成本数据

        Returns:
            更新结果和学习状态
        """
        return await self._historian.update_actual_cost(input_data)
