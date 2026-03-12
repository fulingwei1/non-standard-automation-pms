# -*- coding: utf-8 -*-
"""
技术参数模板服务

提供技术参数模板的CRUD操作、模板匹配和成本估算功能
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models.presale import TechnicalParameterTemplate

logger = logging.getLogger(__name__)


class TechnicalParameterService:
    """技术参数模板服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CRUD 操作 ====================

    def create_template(
        self,
        name: str,
        code: str,
        industry: str,
        test_type: str,
        created_by: int,
        description: Optional[str] = None,
        parameters: Optional[Dict] = None,
        cost_factors: Optional[Dict] = None,
        typical_labor_hours: Optional[Dict] = None,
        reference_docs: Optional[List] = None,
        sample_images: Optional[List] = None,
    ) -> TechnicalParameterTemplate:
        """创建技术参数模板"""
        template = TechnicalParameterTemplate(
            name=name,
            code=code,
            industry=industry,
            test_type=test_type,
            description=description,
            parameters=parameters or {},
            cost_factors=cost_factors or {},
            typical_labor_hours=typical_labor_hours or {},
            reference_docs=reference_docs or [],
            sample_images=sample_images or [],
            created_by=created_by,
            is_active=True,
            use_count=0,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        logger.info(f"创建技术参数模板: {code} - {name}")
        return template

    def get_template_by_id(self, template_id: int) -> Optional[TechnicalParameterTemplate]:
        """根据ID获取模板"""
        return self.db.query(TechnicalParameterTemplate).filter(
            TechnicalParameterTemplate.id == template_id
        ).first()

    def get_template_by_code(self, code: str) -> Optional[TechnicalParameterTemplate]:
        """根据编码获取模板"""
        return self.db.query(TechnicalParameterTemplate).filter(
            TechnicalParameterTemplate.code == code
        ).first()

    def update_template(
        self,
        template_id: int,
        **kwargs
    ) -> Optional[TechnicalParameterTemplate]:
        """更新模板"""
        template = self.get_template_by_id(template_id)
        if not template:
            return None

        # 允许更新的字段
        allowed_fields = {
            "name", "description", "parameters", "cost_factors",
            "typical_labor_hours", "reference_docs", "sample_images", "is_active"
        }

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(template, key, value)

        self.db.commit()
        self.db.refresh(template)
        logger.info(f"更新技术参数模板: {template.code}")
        return template

    def delete_template(self, template_id: int) -> bool:
        """删除模板（软删除）"""
        template = self.get_template_by_id(template_id)
        if not template:
            return False

        template.is_active = False
        self.db.commit()
        logger.info(f"删除技术参数模板: {template.code}")
        return True

    def list_templates(
        self,
        industry: Optional[str] = None,
        test_type: Optional[str] = None,
        is_active: bool = True,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[TechnicalParameterTemplate], int]:
        """
        列出模板

        Args:
            industry: 行业筛选
            test_type: 测试类型筛选
            is_active: 是否只查询启用的模板
            keyword: 关键词搜索（名称、描述）
            page: 页码
            page_size: 每页数量

        Returns:
            (模板列表, 总数)
        """
        query = self.db.query(TechnicalParameterTemplate)

        if is_active is not None:
            query = query.filter(TechnicalParameterTemplate.is_active == is_active)

        if industry:
            query = query.filter(TechnicalParameterTemplate.industry == industry)

        if test_type:
            query = query.filter(TechnicalParameterTemplate.test_type == test_type)

        if keyword:
            keyword_filter = f"%{keyword}%"
            query = query.filter(
                or_(
                    TechnicalParameterTemplate.name.ilike(keyword_filter),
                    TechnicalParameterTemplate.description.ilike(keyword_filter),
                    TechnicalParameterTemplate.code.ilike(keyword_filter),
                )
            )

        total = query.count()
        templates = (
            query
            .order_by(desc(TechnicalParameterTemplate.use_count))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return templates, total

    # ==================== 模板匹配 ====================

    def match_templates(
        self,
        industry: str,
        test_type: str,
        top_k: int = 5,
    ) -> List[TechnicalParameterTemplate]:
        """
        根据行业和测试类型匹配模板

        Args:
            industry: 行业
            test_type: 测试类型
            top_k: 返回前K个匹配结果

        Returns:
            匹配的模板列表，按使用次数排序
        """
        # 精确匹配
        exact_matches = (
            self.db.query(TechnicalParameterTemplate)
            .filter(
                and_(
                    TechnicalParameterTemplate.is_active == True,
                    TechnicalParameterTemplate.industry == industry,
                    TechnicalParameterTemplate.test_type == test_type,
                )
            )
            .order_by(desc(TechnicalParameterTemplate.use_count))
            .limit(top_k)
            .all()
        )

        if len(exact_matches) >= top_k:
            return exact_matches

        # 部分匹配 - 同行业
        remaining = top_k - len(exact_matches)
        industry_matches = (
            self.db.query(TechnicalParameterTemplate)
            .filter(
                and_(
                    TechnicalParameterTemplate.is_active == True,
                    TechnicalParameterTemplate.industry == industry,
                    TechnicalParameterTemplate.test_type != test_type,
                )
            )
            .order_by(desc(TechnicalParameterTemplate.use_count))
            .limit(remaining)
            .all()
        )

        return exact_matches + industry_matches

    def increment_use_count(self, template_id: int) -> None:
        """增加模板使用次数"""
        template = self.get_template_by_id(template_id)
        if template:
            template.use_count = (template.use_count or 0) + 1
            self.db.commit()

    # ==================== 成本估算 ====================

    def estimate_cost(
        self,
        template_id: int,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        基于模板和参数估算成本

        Args:
            template_id: 模板ID
            parameters: 用户输入的技术参数

        Returns:
            成本估算结果，包含总成本、分类成本、工时估算等
        """
        template = self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        cost_factors = template.cost_factors or {}
        base_cost = Decimal(str(cost_factors.get("base_cost", 50000)))
        factors = cost_factors.get("factors", {})
        category_ratios = cost_factors.get("category_ratios", {
            "MECHANICAL": 0.35,
            "ELECTRICAL": 0.30,
            "SOFTWARE": 0.15,
            "OUTSOURCE": 0.10,
            "LABOR": 0.10,
        })

        # 计算成本调整
        total_adjustment = Decimal("0")

        for param_key, factor_config in factors.items():
            if param_key not in parameters:
                continue

            param_value = parameters[param_key]
            factor_type = factor_config.get("type", "linear")
            coefficient = Decimal(str(factor_config.get("coefficient", 0)))

            if factor_type == "linear":
                # 线性因子: adjustment = coefficient * value
                adjustment = coefficient * Decimal(str(param_value))
            elif factor_type == "inverse":
                # 反比因子: adjustment = coefficient * (base / value - 1)
                # 用于节拍时间等，值越小成本越高
                factor_base = Decimal(str(factor_config.get("base", 1)))
                if param_value > 0:
                    adjustment = coefficient * (factor_base / Decimal(str(param_value)) - 1)
                else:
                    adjustment = Decimal("0")
            elif factor_type == "exponential":
                # 指数因子: adjustment = coefficient * (base / value) ^ 2
                # 用于精度等，值越小成本指数增长
                factor_base = Decimal(str(factor_config.get("base", 1)))
                if param_value > 0:
                    ratio = float(factor_base) / float(param_value)
                    adjustment = coefficient * Decimal(str(ratio ** 2))
                else:
                    adjustment = Decimal("0")
            else:
                adjustment = Decimal("0")

            total_adjustment += adjustment

        # 计算总成本
        total_cost = base_cost + total_adjustment
        total_cost = max(total_cost, Decimal("10000"))  # 最低成本1万

        # 按类别分解成本
        cost_breakdown = {}
        for category, ratio in category_ratios.items():
            cost_breakdown[category] = {
                "ratio": ratio,
                "amount": float(total_cost * Decimal(str(ratio))),
            }

        # 工时估算
        labor_hours = template.typical_labor_hours or {}
        total_hours = sum(labor_hours.values())

        # 增加使用次数
        self.increment_use_count(template_id)

        return {
            "template_id": template_id,
            "template_name": template.name,
            "template_code": template.code,
            "base_cost": float(base_cost),
            "adjustment": float(total_adjustment),
            "total_cost": float(total_cost),
            "cost_breakdown": cost_breakdown,
            "labor_hours": {
                "detail": labor_hours,
                "total": total_hours,
            },
            "parameters_used": parameters,
            "estimated_at": datetime.now().isoformat(),
        }

    def batch_estimate_costs(
        self,
        industry: str,
        test_type: str,
        parameters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        批量估算多个模板的成本

        用于对比不同模板的成本差异

        Args:
            industry: 行业
            test_type: 测试类型
            parameters: 技术参数

        Returns:
            多个模板的成本估算结果
        """
        templates = self.match_templates(industry, test_type, top_k=5)
        results = []

        for template in templates:
            try:
                result = self.estimate_cost(template.id, parameters)
                results.append(result)
            except Exception as e:
                logger.warning(f"估算模板 {template.code} 成本失败: {e}")
                continue

        # 按总成本排序
        results.sort(key=lambda x: x["total_cost"])
        return results

    # ==================== 统计分析 ====================

    def get_industry_statistics(self) -> List[Dict[str, Any]]:
        """获取行业统计数据"""
        from sqlalchemy import func

        stats = (
            self.db.query(
                TechnicalParameterTemplate.industry,
                func.count(TechnicalParameterTemplate.id).label("template_count"),
                func.sum(TechnicalParameterTemplate.use_count).label("total_usage"),
            )
            .filter(TechnicalParameterTemplate.is_active == True)
            .group_by(TechnicalParameterTemplate.industry)
            .all()
        )

        return [
            {
                "industry": stat.industry,
                "template_count": stat.template_count,
                "total_usage": stat.total_usage or 0,
            }
            for stat in stats
        ]

    def get_test_type_statistics(self) -> List[Dict[str, Any]]:
        """获取测试类型统计数据"""
        from sqlalchemy import func

        stats = (
            self.db.query(
                TechnicalParameterTemplate.test_type,
                func.count(TechnicalParameterTemplate.id).label("template_count"),
                func.sum(TechnicalParameterTemplate.use_count).label("total_usage"),
            )
            .filter(TechnicalParameterTemplate.is_active == True)
            .group_by(TechnicalParameterTemplate.test_type)
            .all()
        )

        return [
            {
                "test_type": stat.test_type,
                "template_count": stat.template_count,
                "total_usage": stat.total_usage or 0,
            }
            for stat in stats
        ]
