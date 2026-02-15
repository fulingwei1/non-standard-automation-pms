"""
AI智能成本估算服务
"""
import json
import os
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.sales.presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory,
    PresaleCostOptimizationRecord
)
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostEstimationResponse,
    CostOptimizationInput,
    CostOptimizationResponse,
    PricingInput,
    PricingResponse,
    OptimizationSuggestion,
    PricingRecommendation,
    CostBreakdown,
    UpdateActualCostInput,
    HistoricalAccuracyResponse
)


class AICostEstimationService:
    """AI成本估算服务"""
    
    MODEL_VERSION = "v1.0.0"
    
    # 成本系数(可从配置文件读取)
    HARDWARE_MARKUP = Decimal("1.15")  # 硬件加成15%
    SOFTWARE_HOURLY_RATE = Decimal("800")  # 软件开发时薪800元
    INSTALLATION_BASE_COST = Decimal("5000")  # 安装基础成本
    SERVICE_ANNUAL_RATE = Decimal("0.10")  # 年服务费率10%
    RISK_RESERVE_RATE = Decimal("0.08")  # 风险储备金8%
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    async def estimate_cost(self, input_data: CostEstimationInput) -> CostEstimationResponse:
        """
        智能成本估算
        """
        # 1. 计算各项成本
        hardware_cost = self._calculate_hardware_cost(input_data.hardware_items)
        software_cost = self._calculate_software_cost(
            input_data.software_requirements,
            input_data.estimated_man_days
        )
        installation_cost = self._calculate_installation_cost(
            input_data.installation_difficulty,
            hardware_cost
        )
        service_cost = self._calculate_service_cost(
            hardware_cost + software_cost,
            input_data.service_years or 1
        )
        
        # 2. 计算风险储备金(基于历史数据)
        risk_reserve = self._calculate_risk_reserve(
            input_data.project_type,
            input_data.complexity_level,
            hardware_cost + software_cost + installation_cost
        )
        
        total_cost = hardware_cost + software_cost + installation_cost + service_cost + risk_reserve
        
        # 3. 生成优化建议
        optimization_suggestions = await self._generate_optimization_suggestions(
            input_data,
            {
                "hardware_cost": hardware_cost,
                "software_cost": software_cost,
                "installation_cost": installation_cost,
                "service_cost": service_cost,
                "risk_reserve": risk_reserve,
            }
        )
        
        # 4. 生成定价推荐
        pricing_recommendations = self._generate_pricing_recommendations(
            total_cost,
            input_data.target_margin_rate or Decimal("0.30")
        )
        
        # 5. 计算置信度
        confidence_score = self._calculate_confidence_score(input_data)
        
        # 6. 保存到数据库
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
            created_by=self.user_id
        )
        
        self.db.add(estimation)
        self.db.commit()
        self.db.refresh(estimation)
        
        # 7. 构建响应
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
                total_cost=total_cost
            ),
            optimization_suggestions=optimization_suggestions,
            pricing_recommendations=pricing_recommendations,
            confidence_score=confidence_score,
            model_version=self.MODEL_VERSION,
            created_at=estimation.created_at
        )
    
    def _calculate_hardware_cost(self, hardware_items: Optional[List[Dict[str, Any]]]) -> Decimal:
        """计算硬件成本"""
        if not hardware_items:
            return Decimal("0")
        
        total = Decimal("0")
        for item in hardware_items:
            unit_price = Decimal(str(item.get("unit_price", 0)))
            quantity = Decimal(str(item.get("quantity", 1)))
            total += unit_price * quantity
        
        # 加成(运费、损耗等)
        return total * self.HARDWARE_MARKUP
    
    def _calculate_software_cost(self, requirements: Optional[str], man_days: Optional[int]) -> Decimal:
        """计算软件成本"""
        if not man_days:
            # 基于需求描述估算人天(简化版,实际可用AI分析)
            if not requirements:
                return Decimal("0")
            
            word_count = len(requirements)
            if word_count < 100:
                man_days = 5
            elif word_count < 500:
                man_days = 15
            else:
                man_days = 30
        
        # 人天 * 8小时 * 时薪
        return Decimal(str(man_days)) * Decimal("8") * self.SOFTWARE_HOURLY_RATE
    
    def _calculate_installation_cost(self, difficulty: Optional[str], hardware_cost: Decimal) -> Decimal:
        """计算安装调试成本"""
        base_cost = self.INSTALLATION_BASE_COST
        
        if difficulty == "high":
            multiplier = Decimal("2.0")
        elif difficulty == "medium":
            multiplier = Decimal("1.5")
        else:
            multiplier = Decimal("1.0")
        
        # 基础成本 + 硬件成本的5%
        return base_cost * multiplier + hardware_cost * Decimal("0.05")
    
    def _calculate_service_cost(self, base_cost: Decimal, years: int) -> Decimal:
        """计算售后服务成本"""
        return base_cost * self.SERVICE_ANNUAL_RATE * Decimal(str(years))
    
    def _calculate_risk_reserve(self, project_type: str, complexity: str, base_cost: Decimal) -> Decimal:
        """计算风险储备金"""
        rate = self.RISK_RESERVE_RATE
        
        # 基于复杂度调整
        if complexity == "high":
            rate = rate * Decimal("1.5")
        elif complexity == "low":
            rate = rate * Decimal("0.5")
        
        # 从历史数据学习(简化版)
        historical_variance = self._get_historical_variance(project_type)
        if historical_variance:
            rate = rate * (Decimal("1") + historical_variance)
        
        return base_cost * rate
    
    def _get_historical_variance(self, project_type: str) -> Optional[Decimal]:
        """获取历史偏差率"""
        result = self.db.query(
            func.avg(PresaleCostHistory.variance_rate)
        ).filter(
            PresaleCostHistory.project_features.contains(f'"project_type": "{project_type}"')
        ).scalar()
        
        return Decimal(str(result / 100)) if result else None
    
    async def _generate_optimization_suggestions(
        self,
        input_data: CostEstimationInput,
        cost_breakdown: Dict[str, Decimal]
    ) -> List[OptimizationSuggestion]:
        """生成成本优化建议"""
        suggestions = []
        
        # 1. 硬件优化
        if cost_breakdown["hardware_cost"] > Decimal("50000"):
            suggestions.append(OptimizationSuggestion(
                type="hardware",
                description="建议与供应商协商批量采购折扣",
                original_cost=cost_breakdown["hardware_cost"],
                optimized_cost=cost_breakdown["hardware_cost"] * Decimal("0.92"),
                saving_amount=cost_breakdown["hardware_cost"] * Decimal("0.08"),
                saving_rate=Decimal("8.0"),
                feasibility_score=Decimal("0.85"),
                alternative_solutions=["更换为性价比更高的同类产品", "采用分期采购降低单次成本"]
            ))
        
        # 2. 软件优化
        if cost_breakdown["software_cost"] > Decimal("100000"):
            suggestions.append(OptimizationSuggestion(
                type="software",
                description="考虑使用现有代码库模块,减少开发工时",
                original_cost=cost_breakdown["software_cost"],
                optimized_cost=cost_breakdown["software_cost"] * Decimal("0.85"),
                saving_amount=cost_breakdown["software_cost"] * Decimal("0.15"),
                saving_rate=Decimal("15.0"),
                feasibility_score=Decimal("0.75"),
                alternative_solutions=["采用低代码平台", "外包部分非核心功能"]
            ))
        
        # 3. 安装优化
        if input_data.installation_difficulty == "high":
            suggestions.append(OptimizationSuggestion(
                type="installation",
                description="提前进行现场勘查和方案优化,降低安装难度",
                original_cost=cost_breakdown["installation_cost"],
                optimized_cost=cost_breakdown["installation_cost"] * Decimal("0.80"),
                saving_amount=cost_breakdown["installation_cost"] * Decimal("0.20"),
                saving_rate=Decimal("20.0"),
                feasibility_score=Decimal("0.90"),
                alternative_solutions=["采用模块化设计", "提供远程技术支持"]
            ))
        
        return suggestions
    
    def _generate_pricing_recommendations(
        self,
        total_cost: Decimal,
        target_margin_rate: Decimal
    ) -> PricingRecommendation:
        """生成定价推荐"""
        # 基于目标毛利率计算建议价格
        suggested_price = total_cost / (Decimal("1") - target_margin_rate)
        
        # 低中高三档
        low = suggested_price * Decimal("0.90")
        medium = suggested_price
        high = suggested_price * Decimal("1.15")
        
        return PricingRecommendation(
            low=low,
            medium=medium,
            high=high,
            suggested_price=suggested_price,
            target_margin_rate=target_margin_rate * Decimal("100"),
            market_analysis="基于行业标准毛利率和历史成交数据分析"
        )
    
    def _calculate_confidence_score(self, input_data: CostEstimationInput) -> Decimal:
        """计算置信度评分"""
        score = Decimal("0.5")  # 基础分
        
        # 硬件清单完整度
        if input_data.hardware_items and len(input_data.hardware_items) > 0:
            score += Decimal("0.2")
        
        # 软件需求明确度
        if input_data.software_requirements and len(input_data.software_requirements) > 100:
            score += Decimal("0.15")
        
        # 人天估算
        if input_data.estimated_man_days:
            score += Decimal("0.1")
        
        # 历史数据
        historical_count = self.db.query(PresaleCostHistory).filter(
            PresaleCostHistory.project_features.contains(f'"project_type": "{input_data.project_type}"')
        ).count()
        
        if historical_count > 10:
            score += Decimal("0.05")
        
        return min(score, Decimal("1.0"))
    
    async def optimize_cost(self, input_data: CostOptimizationInput) -> CostOptimizationResponse:
        """成本优化分析"""
        estimation = self.db.query(PresaleAICostEstimation).filter(
            PresaleAICostEstimation.id == input_data.estimation_id
        ).first()
        
        if not estimation:
            raise ValueError(f"估算记录不存在: {input_data.estimation_id}")
        
        # 应用优化建议
        original_total = estimation.total_cost
        optimized_total = original_total
        
        suggestions = []
        if estimation.optimization_suggestions:
            for sug_dict in estimation.optimization_suggestions:
                sug = OptimizationSuggestion(**sug_dict)
                
                # 根据风险接受度过滤
                if self._is_acceptable_risk(sug, input_data.max_risk_level):
                    suggestions.append(sug)
                    optimized_total -= sug.saving_amount
        
        total_saving = original_total - optimized_total
        total_saving_rate = (total_saving / original_total * Decimal("100")) if original_total > 0 else Decimal("0")
        
        return CostOptimizationResponse(
            original_total_cost=original_total,
            optimized_total_cost=optimized_total,
            total_saving=total_saving,
            total_saving_rate=total_saving_rate,
            suggestions=suggestions,
            feasibility_summary=f"共有{len(suggestions)}项优化建议,总体可行性评分: {self._calculate_avg_feasibility(suggestions):.2f}"
        )
    
    def _is_acceptable_risk(self, suggestion: OptimizationSuggestion, max_risk_level: str) -> bool:
        """判断风险是否可接受"""
        if not suggestion.feasibility_score:
            return True
        
        risk_thresholds = {
            "low": Decimal("0.85"),
            "medium": Decimal("0.70"),
            "high": Decimal("0.50")
        }
        
        threshold = risk_thresholds.get(max_risk_level, Decimal("0.70"))
        return suggestion.feasibility_score >= threshold
    
    def _calculate_avg_feasibility(self, suggestions: List[OptimizationSuggestion]) -> Decimal:
        """计算平均可行性"""
        if not suggestions:
            return Decimal("0")
        
        total = sum(s.feasibility_score or Decimal("0") for s in suggestions)
        return total / Decimal(str(len(suggestions)))
    
    async def recommend_pricing(self, input_data: PricingInput) -> PricingResponse:
        """定价推荐"""
        estimation = self.db.query(PresaleAICostEstimation).filter(
            PresaleAICostEstimation.id == input_data.estimation_id
        ).first()
        
        if not estimation:
            raise ValueError(f"估算记录不存在: {input_data.estimation_id}")
        
        # 重新生成定价(考虑市场竞争)
        base_pricing = self._generate_pricing_recommendations(
            estimation.total_cost,
            input_data.target_margin_rate
        )
        
        # 市场竞争调整
        competition_factor = {
            "low": Decimal("1.05"),
            "medium": Decimal("1.0"),
            "high": Decimal("0.95")
        }.get(input_data.market_competition_level, Decimal("1.0"))
        
        adjusted_pricing = PricingRecommendation(
            low=base_pricing.low * competition_factor,
            medium=base_pricing.medium * competition_factor,
            high=base_pricing.high * competition_factor,
            suggested_price=base_pricing.suggested_price * competition_factor,
            target_margin_rate=base_pricing.target_margin_rate,
            market_analysis=f"市场竞争程度: {input_data.market_competition_level}, 建议价格调整系数: {competition_factor}"
        )
        
        # 价格敏感度分析
        sensitivity_analysis = self._analyze_price_sensitivity(
            estimation.total_cost,
            adjusted_pricing,
            input_data.customer_budget
        )
        
        return PricingResponse(
            cost_base=estimation.total_cost,
            pricing_recommendations=adjusted_pricing,
            sensitivity_analysis=sensitivity_analysis,
            competitiveness_score=self._calculate_competitiveness(adjusted_pricing, input_data.customer_budget)
        )
    
    def _analyze_price_sensitivity(
        self,
        cost: Decimal,
        pricing: PricingRecommendation,
        customer_budget: Optional[Decimal]
    ) -> Dict[str, Any]:
        """价格敏感度分析"""
        analysis = {
            "cost_base": float(cost),
            "price_range": {
                "min": float(pricing.low),
                "recommended": float(pricing.medium),
                "max": float(pricing.high)
            },
            "margin_analysis": {
                "low_price_margin": float((pricing.low - cost) / pricing.low * 100),
                "recommended_margin": float((pricing.medium - cost) / pricing.medium * 100),
                "high_price_margin": float((pricing.high - cost) / pricing.high * 100)
            }
        }
        
        if customer_budget:
            analysis["budget_fit"] = {
                "customer_budget": float(customer_budget),
                "fits_low": customer_budget >= pricing.low,
                "fits_recommended": customer_budget >= pricing.medium,
                "fits_high": customer_budget >= pricing.high,
                "recommended_strategy": self._get_pricing_strategy(customer_budget, pricing)
            }
        
        return analysis
    
    def _get_pricing_strategy(self, budget: Decimal, pricing: PricingRecommendation) -> str:
        """获取定价策略"""
        if budget >= pricing.high:
            return "客户预算充足,可报高价档,强调高附加值服务"
        elif budget >= pricing.medium:
            return "客户预算适中,推荐标准报价,平衡利润与成交率"
        elif budget >= pricing.low:
            return "客户预算偏紧,可考虑低价档,但需简化部分服务"
        else:
            return "客户预算低于成本,建议优化方案或放弃该项目"
    
    def _calculate_competitiveness(
        self,
        pricing: PricingRecommendation,
        customer_budget: Optional[Decimal]
    ) -> Decimal:
        """计算竞争力评分"""
        if not customer_budget:
            return Decimal("0.70")  # 默认中等竞争力
        
        if customer_budget >= pricing.medium:
            return Decimal("0.90")
        elif customer_budget >= pricing.low:
            return Decimal("0.75")
        else:
            return Decimal("0.50")
    
    async def get_historical_accuracy(self) -> HistoricalAccuracyResponse:
        """获取历史预测准确度"""
        histories = self.db.query(PresaleCostHistory).all()
        
        if not histories:
            return HistoricalAccuracyResponse(
                total_predictions=0,
                average_variance_rate=Decimal("0"),
                accuracy_rate=Decimal("0"),
                recent_trend="无数据"
            )
        
        total = len(histories)
        variance_rates = [h.variance_rate for h in histories if h.variance_rate is not None]
        avg_variance = sum(variance_rates) / len(variance_rates) if variance_rates else Decimal("0")
        
        # 计算准确率(偏差<15%的比例)
        accurate_count = sum(1 for vr in variance_rates if abs(vr) < Decimal("15"))
        accuracy_rate = Decimal(str(accurate_count)) / Decimal(str(len(variance_rates))) * Decimal("100") if variance_rates else Decimal("0")
        
        return HistoricalAccuracyResponse(
            total_predictions=total,
            average_variance_rate=avg_variance,
            accuracy_rate=accuracy_rate,
            best_performing_category="待分析",
            worst_performing_category="待分析",
            recent_trend="稳定",
            sample_cases=None
        )
    
    async def update_actual_cost(self, input_data: UpdateActualCostInput) -> Dict[str, Any]:
        """更新实际成本(用于学习)"""
        estimation = self.db.query(PresaleAICostEstimation).filter(
            PresaleAICostEstimation.id == input_data.estimation_id
        ).first()
        
        if not estimation:
            raise ValueError(f"估算记录不存在: {input_data.estimation_id}")
        
        # 计算偏差率
        variance = input_data.actual_cost - estimation.total_cost
        variance_rate = (variance / estimation.total_cost * Decimal("100")) if estimation.total_cost > 0 else Decimal("0")
        
        # 创建历史记录
        history = PresaleCostHistory(
            project_id=input_data.project_id,
            project_name=input_data.project_name,
            estimated_cost=estimation.total_cost,
            actual_cost=input_data.actual_cost,
            variance_rate=variance_rate,
            cost_breakdown=input_data.actual_breakdown.dict() if input_data.actual_breakdown else None,
            variance_analysis={
                "total_variance": float(variance),
                "variance_rate": float(variance_rate),
                "estimation_id": estimation.id
            },
            project_features=estimation.input_parameters
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return {
            "history_id": history.id,
            "variance_rate": variance_rate,
            "variance_analysis": history.variance_analysis,
            "learning_applied": True,
            "message": "实际成本已记录,模型将从此数据学习"
        }
