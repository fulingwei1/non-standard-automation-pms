# -*- coding: utf-8 -*-
"""
商机健康度评分服务

基于多维度指标评估商机健康状态：
1. 跟进活跃度 - 最近跟进频率
2. 阶段停留时间 - 是否超期滞留
3. 信息完整度 - 关键字段填写情况
4. 客户互动度 - 客户响应情况
5. 风险因素 - 潜在风险评估
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.sales import Contract, Lead, Opportunity, Quote

logger = logging.getLogger(__name__)


class HealthLevel(str, Enum):
    """健康等级"""
    EXCELLENT = "excellent"    # 优秀 (80-100)
    GOOD = "good"              # 良好 (60-79)
    WARNING = "warning"        # 警告 (40-59)
    CRITICAL = "critical"      # 危险 (0-39)


class HealthDimension(str, Enum):
    """健康维度"""
    ACTIVITY = "activity"           # 跟进活跃度
    STAGE_PROGRESS = "stage"        # 阶段进展
    COMPLETENESS = "completeness"   # 信息完整度
    ENGAGEMENT = "engagement"       # 客户互动
    RISK = "risk"                   # 风险因素


@dataclass
class DimensionScore:
    """维度得分"""
    dimension: HealthDimension
    score: int                # 0-100
    weight: float             # 权重
    level: HealthLevel
    details: str              # 详细说明
    suggestions: List[str]    # 改进建议


@dataclass
class OpportunityHealth:
    """商机健康度"""
    opportunity_id: int
    opportunity_code: str
    opportunity_name: str
    customer_name: str
    stage: str
    est_amount: Optional[float]
    # 总体得分
    total_score: int
    health_level: HealthLevel
    # 各维度得分
    dimension_scores: List[DimensionScore]
    # 关键问题
    key_issues: List[str]
    # 改进建议
    top_suggestions: List[str]
    # 最后更新
    last_activity_at: Optional[datetime]
    days_in_stage: int


# 阶段停留时间阈值（天）
STAGE_TIME_THRESHOLDS = {
    "DISCOVERY": {"warning": 14, "critical": 21},
    "QUALIFICATION": {"warning": 10, "critical": 14},
    "PROPOSAL": {"warning": 7, "critical": 10},
    "NEGOTIATION": {"warning": 5, "critical": 7},
    "default": {"warning": 10, "critical": 14},
}

# 维度权重配置
DIMENSION_WEIGHTS = {
    HealthDimension.ACTIVITY: 0.25,
    HealthDimension.STAGE_PROGRESS: 0.25,
    HealthDimension.COMPLETENESS: 0.20,
    HealthDimension.ENGAGEMENT: 0.15,
    HealthDimension.RISK: 0.15,
}

# 必填字段配置
REQUIRED_FIELDS = [
    ("customer_id", "客户"),
    ("opp_name", "商机名称"),
    ("est_amount", "预估金额"),
    ("expected_close_date", "预计成交日期"),
    ("project_type", "项目类型"),
    ("probability", "成交概率"),
]


class OpportunityHealthService:
    """
    商机健康度评分服务

    提供商机健康状态评估，帮助业务员：
    1. 快速识别问题商机
    2. 了解改进方向
    3. 优化跟进策略

    Usage:
        service = OpportunityHealthService(db)
        health = service.get_opportunity_health(opp_id=1)
        print(f"健康度: {health.total_score} ({health.health_level})")
    """

    def __init__(self, db: Session):
        self.db = db

    def get_opportunity_health(self, opp_id: int) -> Optional[OpportunityHealth]:
        """
        获取单个商机的健康度评分

        Args:
            opp_id: 商机ID

        Returns:
            商机健康度评估结果
        """
        opportunity = (
            self.db.query(Opportunity)
            .options(
                joinedload(Opportunity.customer),
                joinedload(Opportunity.owner),
                joinedload(Opportunity.lead),
            )
            .filter(Opportunity.id == opp_id)
            .first()
        )

        if not opportunity:
            return None

        return self._calculate_health(opportunity)

    def get_user_opportunities_health(
        self,
        user_id: int,
        include_closed: bool = False,
        limit: int = 50,
    ) -> List[OpportunityHealth]:
        """
        获取用户所有商机的健康度

        Args:
            user_id: 用户ID
            include_closed: 是否包含已关闭商机
            limit: 返回数量限制

        Returns:
            按健康度排序的商机列表（问题商机优先）
        """
        query = (
            self.db.query(Opportunity)
            .options(
                joinedload(Opportunity.customer),
                joinedload(Opportunity.owner),
            )
            .filter(Opportunity.owner_id == user_id)
        )

        if not include_closed:
            query = query.filter(
                Opportunity.stage.notin_(["CLOSED_WON", "CLOSED_LOST"])
            )

        opportunities = query.all()

        # 计算每个商机的健康度
        health_list = []
        for opp in opportunities:
            health = self._calculate_health(opp)
            if health:
                health_list.append(health)

        # 按得分升序排序（问题商机优先）
        health_list.sort(key=lambda h: h.total_score)

        return health_list[:limit]

    def _calculate_health(self, opp: Opportunity) -> OpportunityHealth:
        """计算商机健康度"""
        dimension_scores = []
        key_issues = []
        all_suggestions = []

        # 1. 计算跟进活跃度
        activity_score = self._calculate_activity_score(opp)
        dimension_scores.append(activity_score)
        if activity_score.score < 60:
            key_issues.append(activity_score.details)
        all_suggestions.extend(activity_score.suggestions)

        # 2. 计算阶段进展
        stage_score = self._calculate_stage_score(opp)
        dimension_scores.append(stage_score)
        if stage_score.score < 60:
            key_issues.append(stage_score.details)
        all_suggestions.extend(stage_score.suggestions)

        # 3. 计算信息完整度
        completeness_score = self._calculate_completeness_score(opp)
        dimension_scores.append(completeness_score)
        if completeness_score.score < 60:
            key_issues.append(completeness_score.details)
        all_suggestions.extend(completeness_score.suggestions)

        # 4. 计算客户互动度
        engagement_score = self._calculate_engagement_score(opp)
        dimension_scores.append(engagement_score)
        if engagement_score.score < 60:
            key_issues.append(engagement_score.details)
        all_suggestions.extend(engagement_score.suggestions)

        # 5. 计算风险因素
        risk_score = self._calculate_risk_score(opp)
        dimension_scores.append(risk_score)
        if risk_score.score < 60:
            key_issues.append(risk_score.details)
        all_suggestions.extend(risk_score.suggestions)

        # 计算加权总分
        total_score = sum(
            ds.score * DIMENSION_WEIGHTS[ds.dimension]
            for ds in dimension_scores
        )
        total_score = int(round(total_score))

        # 确定健康等级
        health_level = self._get_health_level(total_score)

        # 计算阶段停留天数
        days_in_stage = (datetime.now() - opp.updated_at).days if opp.updated_at else 0

        return OpportunityHealth(
            opportunity_id=opp.id,
            opportunity_code=opp.opp_code,
            opportunity_name=opp.opp_name,
            customer_name=opp.customer.customer_name if opp.customer else "未知客户",
            stage=opp.stage,
            est_amount=float(opp.est_amount) if opp.est_amount else None,
            total_score=total_score,
            health_level=health_level,
            dimension_scores=dimension_scores,
            key_issues=key_issues[:3],  # 只取前3个关键问题
            top_suggestions=all_suggestions[:5],  # 只取前5个建议
            last_activity_at=opp.updated_at,
            days_in_stage=days_in_stage,
        )

    def _calculate_activity_score(self, opp: Opportunity) -> DimensionScore:
        """计算跟进活跃度得分"""
        now = datetime.now()
        last_update = opp.updated_at or opp.created_at

        days_since_update = (now - last_update).days if last_update else 999

        # 根据天数计算得分
        if days_since_update <= 3:
            score = 100
            details = "近3天有跟进活动"
        elif days_since_update <= 7:
            score = 80
            details = f"最近跟进在 {days_since_update} 天前"
        elif days_since_update <= 14:
            score = 60
            details = f"已 {days_since_update} 天未跟进"
        elif days_since_update <= 21:
            score = 40
            details = f"⚠️ 已 {days_since_update} 天未跟进"
        else:
            score = 20
            details = f"❌ 已 {days_since_update} 天未跟进，严重滞后"

        suggestions = []
        if score < 80:
            suggestions.append("尽快联系客户，了解最新进展")
        if score < 60:
            suggestions.append("安排本周内进行客户拜访或电话跟进")

        return DimensionScore(
            dimension=HealthDimension.ACTIVITY,
            score=score,
            weight=DIMENSION_WEIGHTS[HealthDimension.ACTIVITY],
            level=self._get_health_level(score),
            details=details,
            suggestions=suggestions,
        )

    def _calculate_stage_score(self, opp: Opportunity) -> DimensionScore:
        """计算阶段进展得分"""
        stage = opp.stage or "default"
        thresholds = STAGE_TIME_THRESHOLDS.get(stage, STAGE_TIME_THRESHOLDS["default"])

        last_update = opp.updated_at or opp.created_at
        days_in_stage = (datetime.now() - last_update).days if last_update else 0

        warning_days = thresholds["warning"]
        critical_days = thresholds["critical"]

        if days_in_stage <= warning_days // 2:
            score = 100
            details = f"{stage} 阶段进展正常"
        elif days_in_stage <= warning_days:
            score = 80
            details = f"{stage} 阶段已 {days_in_stage} 天"
        elif days_in_stage <= critical_days:
            score = 50
            details = f"⚠️ {stage} 阶段停留 {days_in_stage} 天，接近超期"
        else:
            score = 20
            details = f"❌ {stage} 阶段停留 {days_in_stage} 天，已超期"

        suggestions = []
        if score < 80:
            suggestions.append(f"推动商机进入下一阶段")
        if score < 60:
            suggestions.append("分析停滞原因，制定推进计划")
            suggestions.append("考虑是否需要调整策略或寻求支持")

        return DimensionScore(
            dimension=HealthDimension.STAGE_PROGRESS,
            score=score,
            weight=DIMENSION_WEIGHTS[HealthDimension.STAGE_PROGRESS],
            level=self._get_health_level(score),
            details=details,
            suggestions=suggestions,
        )

    def _calculate_completeness_score(self, opp: Opportunity) -> DimensionScore:
        """计算信息完整度得分"""
        filled_count = 0
        missing_fields = []

        for field_name, field_label in REQUIRED_FIELDS:
            value = getattr(opp, field_name, None)
            if value is not None and value != "" and value != 0:
                filled_count += 1
            else:
                missing_fields.append(field_label)

        total_fields = len(REQUIRED_FIELDS)
        score = int((filled_count / total_fields) * 100)

        if score >= 100:
            details = "商机信息完整"
        elif score >= 80:
            details = f"缺少 {len(missing_fields)} 项信息"
        else:
            details = f"⚠️ 缺少关键信息: {', '.join(missing_fields[:3])}"

        suggestions = []
        if missing_fields:
            suggestions.append(f"补充以下信息: {', '.join(missing_fields)}")

        return DimensionScore(
            dimension=HealthDimension.COMPLETENESS,
            score=score,
            weight=DIMENSION_WEIGHTS[HealthDimension.COMPLETENESS],
            level=self._get_health_level(score),
            details=details,
            suggestions=suggestions,
        )

    def _calculate_engagement_score(self, opp: Opportunity) -> DimensionScore:
        """计算客户互动度得分"""
        # 检查是否有报价
        quote_count = (
            self.db.query(func.count(Quote.id))
            .filter(Quote.opportunity_id == opp.id)
            .scalar()
        )

        # 检查成交概率
        probability = opp.probability or 0

        # 综合评分
        score = 50  # 基础分

        if quote_count > 0:
            score += 25  # 有报价加分
        if probability >= 50:
            score += 15  # 高概率加分
        elif probability >= 30:
            score += 10

        # 根据阶段调整
        if opp.stage in ["PROPOSAL", "NEGOTIATION"]:
            if quote_count == 0:
                score -= 20  # 后期阶段无报价扣分

        score = max(0, min(100, score))

        if score >= 80:
            details = "客户互动良好"
        elif score >= 60:
            details = "客户互动一般"
        else:
            details = "⚠️ 客户互动不足"

        suggestions = []
        if quote_count == 0 and opp.stage in ["QUALIFICATION", "PROPOSAL", "NEGOTIATION"]:
            suggestions.append("考虑提供初步报价方案")
        if probability < 30:
            suggestions.append("深入了解客户需求，提升成交可能性")

        return DimensionScore(
            dimension=HealthDimension.ENGAGEMENT,
            score=score,
            weight=DIMENSION_WEIGHTS[HealthDimension.ENGAGEMENT],
            level=self._get_health_level(score),
            details=details,
            suggestions=suggestions,
        )

    def _calculate_risk_score(self, opp: Opportunity) -> DimensionScore:
        """计算风险因素得分"""
        risk_factors = []
        score = 100  # 从满分开始扣分

        # 检查预计成交日期
        if opp.expected_close_date:
            days_to_close = (opp.expected_close_date - datetime.now().date()).days
            if days_to_close < 0:
                score -= 30
                risk_factors.append("预计成交日期已过")
            elif days_to_close < 7:
                score -= 15
                risk_factors.append("预计成交日期临近")

        # 检查金额变化（如果有历史记录）
        # 这里简化处理，实际可以比较历史版本

        # 检查风险等级字段
        if opp.risk_level == "HIGH":
            score -= 25
            risk_factors.append("标记为高风险")
        elif opp.risk_level == "MEDIUM":
            score -= 10
            risk_factors.append("存在中等风险")

        # 检查概率
        if opp.probability and opp.probability < 20:
            score -= 15
            risk_factors.append("成交概率较低")

        score = max(0, min(100, score))

        if not risk_factors:
            details = "暂无明显风险"
        else:
            details = f"风险因素: {', '.join(risk_factors)}"

        suggestions = []
        if "预计成交日期已过" in risk_factors:
            suggestions.append("更新预计成交日期，重新评估商机状态")
        if "高风险" in str(risk_factors):
            suggestions.append("制定风险应对计划")

        return DimensionScore(
            dimension=HealthDimension.RISK,
            score=score,
            weight=DIMENSION_WEIGHTS[HealthDimension.RISK],
            level=self._get_health_level(score),
            details=details,
            suggestions=suggestions,
        )

    def _get_health_level(self, score: int) -> HealthLevel:
        """根据得分确定健康等级"""
        if score >= 80:
            return HealthLevel.EXCELLENT
        elif score >= 60:
            return HealthLevel.GOOD
        elif score >= 40:
            return HealthLevel.WARNING
        else:
            return HealthLevel.CRITICAL

    def get_health_summary(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户商机健康度汇总

        Returns:
            包含各健康等级统计和问题商机列表
        """
        health_list = self.get_user_opportunities_health(user_id, limit=200)

        summary = {
            "total_count": len(health_list),
            "by_level": {
                "excellent": {"count": 0, "amount": 0},
                "good": {"count": 0, "amount": 0},
                "warning": {"count": 0, "amount": 0},
                "critical": {"count": 0, "amount": 0},
            },
            "average_score": 0,
            "problem_opportunities": [],
        }

        total_score = 0
        for health in health_list:
            level_key = health.health_level.value
            summary["by_level"][level_key]["count"] += 1
            summary["by_level"][level_key]["amount"] += health.est_amount or 0
            total_score += health.total_score

            # 收集问题商机
            if health.health_level in [HealthLevel.WARNING, HealthLevel.CRITICAL]:
                summary["problem_opportunities"].append({
                    "id": health.opportunity_id,
                    "code": health.opportunity_code,
                    "name": health.opportunity_name,
                    "score": health.total_score,
                    "level": health.health_level.value,
                    "key_issues": health.key_issues,
                })

        if health_list:
            summary["average_score"] = round(total_score / len(health_list), 1)

        # 只保留前10个问题商机
        summary["problem_opportunities"] = summary["problem_opportunities"][:10]

        return summary
