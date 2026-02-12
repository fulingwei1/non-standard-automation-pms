# -*- coding: utf-8 -*-
"""
项目模板推荐服务

Issue 4.3: 实现智能模板推荐功能，根据项目信息推荐合适的模板
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.project import ProjectTemplate


class TemplateRecommendationService:
    """项目模板推荐服务"""

    def __init__(self, db: Session):
        self.db = db

    def recommend_templates(
        self,
        project_type: Optional[str] = None,
        product_category: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        根据项目信息推荐合适的模板

        Args:
            project_type: 项目类型
            product_category: 产品类别
            industry: 行业
            limit: 返回推荐数量（默认5个）

        Returns:
            List[Dict]: 推荐模板列表，包含推荐理由和评分
        """
        query = self.db.query(ProjectTemplate).filter(
            ProjectTemplate.is_active
        )

        recommendations = []

        # 1. 根据项目类型推荐
        if project_type:
            type_matches = query.filter(
                ProjectTemplate.project_type == project_type
            ).all()
            for template in type_matches:
                score = self._calculate_score(template, project_type, product_category, industry)
                recommendations.append({
                    "template_id": template.id,
                    "template_code": template.template_code,
                    "template_name": template.template_name,
                    "description": template.description,
                    "score": score,
                    "reasons": self._get_recommendation_reasons(template, project_type, product_category, industry),
                    "match_type": "project_type"
                })

        # 2. 根据产品类别推荐
        if product_category:
            category_matches = query.filter(
                ProjectTemplate.product_category == product_category
            ).all()
            for template in category_matches:
                # 避免重复添加
                if not any(r["template_id"] == template.id for r in recommendations):
                    score = self._calculate_score(template, project_type, product_category, industry)
                    recommendations.append({
                        "template_id": template.id,
                        "template_code": template.template_code,
                        "template_name": template.template_name,
                        "description": template.description,
                        "score": score,
                        "reasons": self._get_recommendation_reasons(template, project_type, product_category, industry),
                        "match_type": "product_category"
                    })

        # 3. 根据行业推荐
        if industry:
            industry_matches = query.filter(
                ProjectTemplate.industry == industry
            ).all()
            for template in industry_matches:
                # 避免重复添加
                if not any(r["template_id"] == template.id for r in recommendations):
                    score = self._calculate_score(template, project_type, product_category, industry)
                    recommendations.append({
                        "template_id": template.id,
                        "template_code": template.template_code,
                        "template_name": template.template_name,
                        "description": template.description,
                        "score": score,
                        "reasons": self._get_recommendation_reasons(template, project_type, product_category, industry),
                        "match_type": "industry"
                    })

        # 4. 根据使用频率推荐（如果没有匹配的，推荐使用最多的模板）
        if not recommendations:
            popular_templates = query.order_by(
                desc(ProjectTemplate.usage_count)
            ).limit(limit).all()

            for template in popular_templates:
                score = self._calculate_score(template, project_type, product_category, industry)
                recommendations.append({
                    "template_id": template.id,
                    "template_code": template.template_code,
                    "template_name": template.template_name,
                    "description": template.description,
                    "score": score,
                    "reasons": ["使用频率高（推荐热门模板）"],
                    "match_type": "usage_frequency"
                })

        # 按评分排序，返回前limit个
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    def _calculate_score(
        self,
        template: ProjectTemplate,
        project_type: Optional[str],
        product_category: Optional[str],
        industry: Optional[str]
    ) -> float:
        """
        计算模板推荐评分

        评分规则：
        - 项目类型匹配：+30分
        - 产品类别匹配：+25分
        - 行业匹配：+20分
        - 使用频率：+15分（使用次数越多，分数越高，最高15分）
        - 基础分：10分
        """
        score = 10.0  # 基础分

        # 项目类型匹配
        if project_type and template.project_type == project_type:
            score += 30.0

        # 产品类别匹配
        if product_category and template.product_category == product_category:
            score += 25.0

        # 行业匹配
        if industry and template.industry == industry:
            score += 20.0

        # 使用频率加分（使用次数越多，分数越高，最高15分）
        usage_count = template.usage_count or 0
        if usage_count > 0:
            # 使用对数函数，使分数增长更平滑
            import math
            usage_score = min(15.0, math.log10(usage_count + 1) * 5)
            score += usage_score

        return round(score, 2)

    def _get_recommendation_reasons(
        self,
        template: ProjectTemplate,
        project_type: Optional[str],
        product_category: Optional[str],
        industry: Optional[str]
    ) -> List[str]:
        """
        获取推荐理由列表
        """
        reasons = []

        if project_type and template.project_type == project_type:
            reasons.append(f"项目类型匹配：{project_type}")

        if product_category and template.product_category == product_category:
            reasons.append(f"产品类别匹配：{product_category}")

        if industry and template.industry == industry:
            reasons.append(f"行业匹配：{industry}")

        if template.usage_count and template.usage_count > 0:
            reasons.append(f"使用频率高（已使用 {template.usage_count} 次）")

        if not reasons:
            reasons.append("通用模板推荐")

        return reasons
