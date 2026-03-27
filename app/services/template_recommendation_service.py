# -*- coding: utf-8 -*-
"""
项目模板智能推荐服务

根据客户类型、产品类型、合同金额和历史成功模式推荐模板
"""

import math
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.models.project import Customer, Project, ProjectTemplate


# 合同金额分级阈值
AMOUNT_TIER_LARGE = 500_000  # >=50万为大项目
AMOUNT_TIER_SMALL = 100_000  # <10万为小项目


class TemplateRecommendationService:
    """项目模板智能推荐服务"""

    def __init__(self, db: Session):
        self.db = db

    def recommend_templates(
        self,
        project_type: Optional[str] = None,
        product_category: Optional[str] = None,
        industry: Optional[str] = None,
        customer_id: Optional[int] = None,
        contract_amount: Optional[float] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        智能推荐模板 — 综合客户类型、产品类型、合同金额、历史成功模式

        Returns:
            recommended_templates[] 含 score + reasons
        """
        templates = (
            self.db.query(ProjectTemplate)
            .filter(ProjectTemplate.is_active == True)  # noqa: E712
            .all()
        )
        if not templates:
            return []

        # 预加载客户信息
        customer = None
        if customer_id:
            customer = self.db.query(Customer).get(customer_id)

        # 获取历史成功模式
        history_patterns = self._get_history_patterns(customer_id, product_category, industry)

        recommendations = []
        for template in templates:
            score, reasons = self._score_template(
                template,
                project_type=project_type,
                product_category=product_category,
                industry=industry,
                customer=customer,
                contract_amount=contract_amount,
                history_patterns=history_patterns,
            )
            recommendations.append(
                {
                    "template_id": template.id,
                    "template_code": template.template_code,
                    "template_name": template.template_name,
                    "description": template.description,
                    "project_type": template.project_type,
                    "product_category": template.product_category,
                    "industry": template.industry,
                    "usage_count": template.usage_count or 0,
                    "score": score,
                    "reasons": reasons,
                }
            )

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    # ------------------------------------------------------------------
    # 综合评分
    # ------------------------------------------------------------------
    def _score_template(
        self,
        template: ProjectTemplate,
        *,
        project_type: Optional[str],
        product_category: Optional[str],
        industry: Optional[str],
        customer: Optional[Customer],
        contract_amount: Optional[float],
        history_patterns: Dict[int, Dict],
    ) -> tuple:
        """返回 (score, reasons)"""
        score = 10.0  # 基础分
        reasons: List[str] = []

        # 1) 项目类型匹配 +30
        if project_type and template.project_type == project_type:
            score += 30.0
            reasons.append(f"项目类型匹配：{project_type}")

        # 2) 产品类别匹配 +25
        if product_category and template.product_category == product_category:
            score += 25.0
            reasons.append(f"产品类别匹配：{product_category}")

        # 3) 行业匹配 +20
        if industry and template.industry == industry:
            score += 20.0
            reasons.append(f"行业匹配：{industry}")

        # 4) 客户类型匹配 +15
        customer_score, customer_reason = self._score_customer_match(template, customer)
        if customer_score > 0:
            score += customer_score
            reasons.append(customer_reason)

        # 5) 合同金额复杂度匹配 +10
        amount_score, amount_reason = self._score_amount_match(template, contract_amount)
        if amount_score > 0:
            score += amount_score
            reasons.append(amount_reason)

        # 6) 历史成功模式 +20
        if template.id in history_patterns:
            hp = history_patterns[template.id]
            score += hp["score"]
            reasons.append(hp["reason"])

        # 7) 使用频率 +15 (对数衰减)
        usage_count = template.usage_count or 0
        if usage_count > 0:
            usage_score = min(15.0, math.log10(usage_count + 1) * 5)
            score += usage_score

        if not reasons:
            reasons.append("通用模板推荐")

        return round(score, 2), reasons

    # ------------------------------------------------------------------
    # 客户类型评分
    # ------------------------------------------------------------------
    def _score_customer_match(
        self, template: ProjectTemplate, customer: Optional[Customer]
    ) -> tuple:
        """根据客户类型（老客户/新客户/行业）匹配"""
        if not customer:
            return 0, ""

        # 老客户 — cooperation_years > 0
        is_repeat = (customer.cooperation_years or 0) > 0

        # 老客户偏好之前用过的模板
        if is_repeat:
            used = (
                self.db.query(Project.template_id)
                .filter(
                    Project.customer_id == customer.id,
                    Project.template_id == template.id,
                )
                .first()
            )
            if used:
                return 15.0, f"老客户 {customer.customer_name} 曾使用此模板"

        # 行业匹配
        if customer.industry and template.industry == customer.industry:
            label = "老客户" if is_repeat else "新客户"
            return 10.0, f"{label}行业匹配（{customer.industry}）"

        # 客户等级匹配 — A 级大客户偏好复杂模板
        if customer.customer_level == "A":
            # 看模板的平均合同金额
            avg_amount = (
                self.db.query(func.avg(Project.contract_amount))
                .filter(Project.template_id == template.id)
                .scalar()
            )
            if avg_amount and float(avg_amount) >= AMOUNT_TIER_LARGE:
                return 8.0, "A级大客户，推荐大项目模板"

        return 0, ""

    # ------------------------------------------------------------------
    # 合同金额复杂度评分
    # ------------------------------------------------------------------
    def _score_amount_match(
        self, template: ProjectTemplate, contract_amount: Optional[float]
    ) -> tuple:
        """根据合同金额匹配模板复杂度"""
        if not contract_amount:
            return 0, ""

        # 统计该模板历史项目的平均合同金额
        stats = (
            self.db.query(
                func.avg(Project.contract_amount).label("avg_amount"),
                func.count(Project.id).label("cnt"),
            )
            .filter(Project.template_id == template.id)
            .first()
        )

        if not stats or not stats.cnt or stats.cnt == 0:
            return 0, ""

        avg = float(stats.avg_amount or 0)
        if avg == 0:
            return 0, ""

        # 判断当前金额的档次
        if contract_amount >= AMOUNT_TIER_LARGE:
            tier = "large"
            tier_label = "大项目"
        elif contract_amount < AMOUNT_TIER_SMALL:
            tier = "small"
            tier_label = "小项目"
        else:
            tier = "medium"
            tier_label = "中等项目"

        # 模板历史平均金额档次
        if avg >= AMOUNT_TIER_LARGE:
            tmpl_tier = "large"
        elif avg < AMOUNT_TIER_SMALL:
            tmpl_tier = "small"
        else:
            tmpl_tier = "medium"

        if tier == tmpl_tier:
            return 10.0, f"合同金额匹配（{tier_label}，模板历史均值 ¥{avg:,.0f}）"

        return 0, ""

    # ------------------------------------------------------------------
    # 历史成功模式
    # ------------------------------------------------------------------
    def _get_history_patterns(
        self,
        customer_id: Optional[int],
        product_category: Optional[str],
        industry: Optional[str],
    ) -> Dict[int, Dict]:
        """
        查找类似客户/产品曾用过哪些模板且成功交付（stage=S9 或 health=H4）
        返回 {template_id: {"score": float, "reason": str}}
        """
        result: Dict[int, Dict] = {}

        # 构建"类似项目"过滤条件
        filters = [
            Project.template_id.isnot(None),
            Project.stage.in_(["S9"]),  # 已结项
        ]

        similar_desc_parts = []

        if customer_id:
            # 同一客户的成功项目
            customer = self.db.query(Customer).get(customer_id)
            if customer and customer.industry:
                # 同行业客户
                similar_customers = (
                    self.db.query(Customer.id)
                    .filter(Customer.industry == customer.industry)
                    .all()
                )
                cust_ids = [c.id for c in similar_customers]
                if cust_ids:
                    filters.append(Project.customer_id.in_(cust_ids))
                    similar_desc_parts.append(f"同行业({customer.industry})客户")

        if product_category:
            filters.append(Project.product_category == product_category)
            similar_desc_parts.append(f"同类产品({product_category})")

        if industry and not similar_desc_parts:
            filters.append(Project.industry == industry)
            similar_desc_parts.append(f"同行业({industry})")

        if not similar_desc_parts:
            return result

        # 查询成功交付项目的模板使用统计
        rows = (
            self.db.query(
                Project.template_id,
                func.count(Project.id).label("success_count"),
            )
            .filter(and_(*filters))
            .group_by(Project.template_id)
            .order_by(desc("success_count"))
            .limit(10)
            .all()
        )

        desc_text = "、".join(similar_desc_parts)
        for row in rows:
            if row.template_id and row.success_count > 0:
                # 成功次数越多分越高，最高 20 分
                history_score = min(20.0, row.success_count * 5.0)
                result[row.template_id] = {
                    "score": history_score,
                    "reason": f"历史成功复用：{desc_text}已有 {row.success_count} 个成功交付项目使用此模板",
                }

        return result
