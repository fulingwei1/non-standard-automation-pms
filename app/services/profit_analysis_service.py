# -*- coding: utf-8 -*-
"""
项目利润优化分析服务

提供：
1. 毛利率实时分析（当前毛利、预计毛利、与目标对比）
2. 成本优化建议（采购/工时 vs 历史）
3. 报价与成本偏差分析
4. 高利润项目特征分析
5. 低利润项目根因分析
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func, and_, or_, desc
from sqlalchemy.orm import Session

from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project.core import Project
from app.models.project.financial import ProjectCost, FinancialProjectCost
from app.models.sales.contracts import Contract
from app.models.sales.quotes import Quote, QuoteVersion, QuoteItem


# 默认目标毛利率（%）
DEFAULT_TARGET_MARGIN = 25.0


class ProfitAnalysisService:
    """项目利润分析服务"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 1. 毛利率实时分析
    # ------------------------------------------------------------------
    def get_margin_analysis(
        self, project_id: int, target_margin: float = DEFAULT_TARGET_MARGIN
    ) -> Dict[str, Any]:
        """
        实时计算项目毛利率：
        - 当前毛利 = 合同金额 - 已发生成本
        - 预计毛利 = 合同金额 - (已发生 + 预计剩余)
        - 毛利率 = 毛利 / 合同金额
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        contract_amount = float(project.contract_amount or 0)
        budget_amount = float(project.budget_amount or 0)

        # 已发生成本（聚合 project_costs + financial_project_costs）
        actual_cost = self._get_actual_cost(project_id)

        # 预算剩余 = 预算总额 - 已发生成本（如果有预算的话）
        if budget_amount > 0:
            remaining_cost = max(budget_amount - actual_cost, 0)
        else:
            remaining_cost = 0

        forecast_total_cost = actual_cost + remaining_cost

        # 当前毛利
        current_margin = contract_amount - actual_cost
        current_margin_rate = (
            (current_margin / contract_amount * 100) if contract_amount > 0 else 0
        )

        # 预计毛利
        forecast_margin = contract_amount - forecast_total_cost
        forecast_margin_rate = (
            (forecast_margin / contract_amount * 100) if contract_amount > 0 else 0
        )

        # 与目标对比
        margin_gap = current_margin_rate - target_margin
        forecast_gap = forecast_margin_rate - target_margin

        # 健康度判断
        if current_margin_rate >= target_margin:
            health = "healthy"
        elif current_margin_rate >= target_margin * 0.7:
            health = "warning"
        else:
            health = "critical"

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "contract_amount": round(contract_amount, 2),
            "budget_amount": round(budget_amount, 2),
            "actual_cost": round(actual_cost, 2),
            "remaining_cost": round(remaining_cost, 2),
            "forecast_total_cost": round(forecast_total_cost, 2),
            "current_margin": round(current_margin, 2),
            "current_margin_rate": round(current_margin_rate, 2),
            "forecast_margin": round(forecast_margin, 2),
            "forecast_margin_rate": round(forecast_margin_rate, 2),
            "target_margin_rate": target_margin,
            "margin_gap": round(margin_gap, 2),
            "forecast_gap": round(forecast_gap, 2),
            "health": health,
        }

    # ------------------------------------------------------------------
    # 2. 成本优化建议
    # ------------------------------------------------------------------
    def get_cost_optimization(self, project_id: int) -> Dict[str, Any]:
        """
        基于历史数据生成成本优化建议：
        - 采购成本 vs 历史同类项目
        - 工时消耗 vs 预算
        - 识别可优化的成本项
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 当前项目成本分布
        cost_by_type = self._get_cost_by_type(project_id)

        # 获取同类项目（同 project_type / product_category）的平均成本分布
        similar_projects = (
            self.db.query(Project)
            .filter(
                Project.id != project_id,
                Project.contract_amount > 0,
                or_(
                    Project.project_type == project.project_type,
                    Project.product_category == project.product_category,
                ),
            )
            .all()
        )

        suggestions: List[Dict[str, Any]] = []

        if similar_projects:
            # 计算同类项目平均成本占比
            avg_cost_ratio = self._get_avg_cost_ratio(
                [p.id for p in similar_projects]
            )
            contract_amount = float(project.contract_amount or 0)

            for cost_type, amount in cost_by_type.items():
                current_ratio = (
                    (amount / contract_amount * 100) if contract_amount > 0 else 0
                )
                avg_ratio = avg_cost_ratio.get(cost_type, 0)

                if avg_ratio > 0 and current_ratio > avg_ratio * 1.2:
                    # 当前成本占比高于历史平均 20% 以上
                    potential_saving = amount - (contract_amount * avg_ratio / 100)
                    suggestions.append(
                        {
                            "type": "cost_overrun",
                            "cost_type": cost_type,
                            "current_amount": round(amount, 2),
                            "current_ratio": round(current_ratio, 2),
                            "avg_ratio": round(avg_ratio, 2),
                            "potential_saving": round(max(potential_saving, 0), 2),
                            "suggestion": f"{cost_type}成本占比({current_ratio:.1f}%)高于历史平均({avg_ratio:.1f}%)，建议审查",
                            "priority": "high" if current_ratio > avg_ratio * 1.5 else "medium",
                        }
                    )

        # 预算 vs 实际
        budget_amount = float(project.budget_amount or 0)
        actual_cost = self._get_actual_cost(project_id)
        progress = float(project.progress_pct or 0)

        if budget_amount > 0 and progress > 0:
            expected_cost = budget_amount * progress / 100
            if actual_cost > expected_cost * 1.1:
                suggestions.append(
                    {
                        "type": "budget_pace",
                        "cost_type": "overall",
                        "current_amount": round(actual_cost, 2),
                        "expected_amount": round(expected_cost, 2),
                        "overspend": round(actual_cost - expected_cost, 2),
                        "suggestion": f"项目进度{progress:.0f}%，但已消耗预算{actual_cost/budget_amount*100:.0f}%，成本消耗过快",
                        "priority": "high",
                    }
                )

        # 工时分析
        labor_cost = cost_by_type.get("labor", 0) or cost_by_type.get("LABOR", 0)
        labor_budget = self._get_budget_by_category(project_id, "LABOR")
        if labor_budget > 0 and labor_cost > labor_budget * 0.9:
            suggestions.append(
                {
                    "type": "labor_warning",
                    "cost_type": "labor",
                    "current_amount": round(labor_cost, 2),
                    "budget_amount": round(labor_budget, 2),
                    "usage_rate": round(labor_cost / labor_budget * 100, 2),
                    "suggestion": f"人工成本已使用预算的{labor_cost/labor_budget*100:.0f}%，注意控制工时",
                    "priority": "high" if labor_cost > labor_budget else "medium",
                }
            )

        return {
            "project_id": project_id,
            "cost_by_type": [
                {"type": k, "amount": round(v, 2)} for k, v in cost_by_type.items()
            ],
            "similar_project_count": len(similar_projects),
            "optimization_suggestions": suggestions,
        }

    # ------------------------------------------------------------------
    # 3. 报价与成本偏差分析
    # ------------------------------------------------------------------
    def get_quote_cost_variance(self, project_id: int) -> Dict[str, Any]:
        """
        分析报价时预估成本 vs 实际成本的偏差：
        - 偏差最大的成本项
        - 偏差原因归类
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 获取关联报价版本
        contract = (
            self.db.query(Contract)
            .filter(Contract.project_id == project_id)
            .first()
        )

        quote_items: List[Dict[str, Any]] = []
        total_quoted_cost = 0
        total_actual_cost = 0

        if contract and contract.quote_id:
            # quote_id 实际是 quote_version_id
            items = (
                self.db.query(QuoteItem)
                .filter(QuoteItem.quote_version_id == contract.quote_id)
                .all()
            )

            cost_by_type = self._get_cost_by_type(project_id)

            for item in items:
                quoted = float(item.cost or 0) * float(item.qty or 1)
                category = item.cost_category or item.item_type or "其他"
                actual = cost_by_type.get(category, 0)

                variance = actual - quoted
                variance_pct = (variance / quoted * 100) if quoted > 0 else 0

                total_quoted_cost += quoted
                total_actual_cost += actual

                # 偏差原因推断
                reason = "正常偏差"
                if variance_pct > 30:
                    reason = "显著超支（可能设计变更/返工）"
                elif variance_pct > 15:
                    reason = "中度超支（可能采购涨价）"
                elif variance_pct < -15:
                    reason = "节约（优化采购/效率提升）"

                quote_items.append(
                    {
                        "item_name": item.item_name,
                        "cost_category": category,
                        "quoted_cost": round(quoted, 2),
                        "actual_cost": round(actual, 2),
                        "variance": round(variance, 2),
                        "variance_pct": round(variance_pct, 2),
                        "reason": reason,
                    }
                )

            # 按偏差绝对值排序
            quote_items.sort(key=lambda x: abs(x["variance"]), reverse=True)

        overall_variance = total_actual_cost - total_quoted_cost
        overall_variance_pct = (
            (overall_variance / total_quoted_cost * 100) if total_quoted_cost > 0 else 0
        )

        # 偏差原因统计
        reason_summary: Dict[str, int] = {}
        for item in quote_items:
            r = item["reason"]
            reason_summary[r] = reason_summary.get(r, 0) + 1

        return {
            "project_id": project_id,
            "has_quote": bool(contract and contract.quote_id),
            "total_quoted_cost": round(total_quoted_cost, 2),
            "total_actual_cost": round(total_actual_cost, 2),
            "overall_variance": round(overall_variance, 2),
            "overall_variance_pct": round(overall_variance_pct, 2),
            "items": quote_items[:10],  # Top 10
            "reason_summary": [
                {"reason": k, "count": v} for k, v in reason_summary.items()
            ],
        }

    # ------------------------------------------------------------------
    # 4. 高利润项目特征分析
    # ------------------------------------------------------------------
    def get_high_profit_patterns(
        self, min_margin: float = 30.0, limit: int = 20
    ) -> Dict[str, Any]:
        """
        分析高毛利项目的共同特征：
        - 客户类型 / 产品类型 / 团队配置
        - 可复用的成功模式
        """
        # 查询所有有合同金额的已完成/进行中项目
        projects = (
            self.db.query(Project)
            .filter(
                Project.contract_amount > 0,
                Project.actual_cost > 0,
            )
            .all()
        )

        high_profit = []
        all_margins = []

        for p in projects:
            contract = float(p.contract_amount or 0)
            cost = float(p.actual_cost or 0)
            if contract <= 0:
                continue
            margin = (contract - cost) / contract * 100
            all_margins.append(margin)

            if margin >= min_margin:
                high_profit.append(
                    {
                        "project_id": p.id,
                        "project_code": p.project_code,
                        "project_name": p.project_name,
                        "customer_name": p.customer_name,
                        "project_type": p.project_type,
                        "product_category": p.product_category,
                        "industry": p.industry,
                        "contract_amount": contract,
                        "actual_cost": cost,
                        "margin_rate": round(margin, 2),
                    }
                )

        high_profit.sort(key=lambda x: x["margin_rate"], reverse=True)
        high_profit = high_profit[:limit]

        # 提取特征
        patterns = self._extract_patterns(high_profit)

        avg_margin = sum(all_margins) / len(all_margins) if all_margins else 0

        return {
            "total_projects_analyzed": len(projects),
            "high_profit_count": len(high_profit),
            "avg_margin_rate": round(avg_margin, 2),
            "high_profit_threshold": min_margin,
            "high_profit_projects": high_profit,
            "patterns": patterns,
        }

    # ------------------------------------------------------------------
    # 5. 低利润项目根因分析
    # ------------------------------------------------------------------
    def get_low_profit_root_cause(
        self, max_margin: float = 10.0, limit: int = 20
    ) -> Dict[str, Any]:
        """
        分析低毛利项目的主要问题：
        - 早期预警信号
        - 改进建议
        """
        projects = (
            self.db.query(Project)
            .filter(
                Project.contract_amount > 0,
                Project.actual_cost > 0,
            )
            .all()
        )

        low_profit = []

        for p in projects:
            contract = float(p.contract_amount or 0)
            cost = float(p.actual_cost or 0)
            if contract <= 0:
                continue
            margin = (contract - cost) / contract * 100

            if margin <= max_margin:
                # 分析根因
                root_causes = []
                budget = float(p.budget_amount or 0)

                if budget > 0 and cost > budget:
                    root_causes.append(
                        {
                            "cause": "预算超支",
                            "detail": f"实际成本超预算{(cost-budget)/budget*100:.0f}%",
                        }
                    )

                if budget > 0 and budget > contract * 0.9:
                    root_causes.append(
                        {
                            "cause": "预算偏高",
                            "detail": "预算接近或超过合同金额，利润空间不足",
                        }
                    )

                if contract < cost:
                    root_causes.append(
                        {
                            "cause": "成本倒挂",
                            "detail": f"实际成本超合同金额{cost-contract:.0f}元",
                        }
                    )

                if not root_causes:
                    root_causes.append(
                        {
                            "cause": "利润率偏低",
                            "detail": f"毛利率仅{margin:.1f}%，低于阈值{max_margin}%",
                        }
                    )

                low_profit.append(
                    {
                        "project_id": p.id,
                        "project_code": p.project_code,
                        "project_name": p.project_name,
                        "customer_name": p.customer_name,
                        "project_type": p.project_type,
                        "contract_amount": contract,
                        "actual_cost": cost,
                        "margin_rate": round(margin, 2),
                        "root_causes": root_causes,
                    }
                )

        low_profit.sort(key=lambda x: x["margin_rate"])
        low_profit = low_profit[:limit]

        # 早期预警信号
        warning_signals = [
            "项目前30%阶段成本已消耗超过40%预算",
            "采购成本超出报价预估15%以上",
            "频繁的设计变更导致返工",
            "工时消耗速度超出计划",
            "客户需求频繁变更",
        ]

        # 改进建议
        improvements = [
            {"area": "报价管控", "action": "建立报价成本审核机制，确保预留足够利润空间"},
            {"area": "采购优化", "action": "建立供应商价格对比库，优选性价比高的供应商"},
            {"area": "工时管控", "action": "严格执行工时预算，超出需审批"},
            {"area": "变更管理", "action": "建立变更成本评估流程，及时调整合同金额"},
            {"area": "过程监控", "action": "设置毛利率预警线，按月跟踪成本消耗"},
        ]

        return {
            "total_low_profit": len(low_profit),
            "low_profit_threshold": max_margin,
            "low_profit_projects": low_profit,
            "warning_signals": warning_signals,
            "improvements": improvements,
        }

    # ------------------------------------------------------------------
    # 综合利润分析（聚合所有分析结果）
    # ------------------------------------------------------------------
    def get_profit_analysis(
        self,
        project_id: int,
        target_margin: float = DEFAULT_TARGET_MARGIN,
    ) -> Dict[str, Any]:
        """
        综合利润分析 — 聚合毛利率、优化建议、偏差分析
        返回格式：profit_analysis{current_margin, forecast_margin, optimization_suggestions[]}
        """
        margin = self.get_margin_analysis(project_id, target_margin)
        if margin.get("error"):
            return margin

        optimization = self.get_cost_optimization(project_id)
        variance = self.get_quote_cost_variance(project_id)

        return {
            "project_id": project_id,
            "current_margin": margin["current_margin"],
            "current_margin_rate": margin["current_margin_rate"],
            "forecast_margin": margin["forecast_margin"],
            "forecast_margin_rate": margin["forecast_margin_rate"],
            "target_margin_rate": margin["target_margin_rate"],
            "margin_gap": margin["margin_gap"],
            "health": margin["health"],
            "contract_amount": margin["contract_amount"],
            "actual_cost": margin["actual_cost"],
            "remaining_cost": margin["remaining_cost"],
            "forecast_total_cost": margin["forecast_total_cost"],
            "optimization_suggestions": optimization.get(
                "optimization_suggestions", []
            ),
            "quote_variance": {
                "has_quote": variance.get("has_quote", False),
                "overall_variance": variance.get("overall_variance", 0),
                "overall_variance_pct": variance.get("overall_variance_pct", 0),
                "top_variances": variance.get("items", [])[:5],
            },
        }

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------
    def _get_actual_cost(self, project_id: int) -> float:
        """聚合项目已发生成本"""
        # project_costs 表
        r1 = (
            self.db.query(func.sum(ProjectCost.amount))
            .filter(ProjectCost.project_id == project_id)
            .scalar()
        )
        # financial_project_costs 表
        r2 = (
            self.db.query(func.sum(FinancialProjectCost.amount))
            .filter(FinancialProjectCost.project_id == project_id)
            .scalar()
        )
        return float(r1 or 0) + float(r2 or 0)

    def _get_cost_by_type(self, project_id: int) -> Dict[str, float]:
        """按类型汇总成本"""
        rows = (
            self.db.query(
                ProjectCost.cost_type, func.sum(ProjectCost.amount).label("total")
            )
            .filter(ProjectCost.project_id == project_id)
            .group_by(ProjectCost.cost_type)
            .all()
        )
        result = {(r[0] or "其他"): float(r[1] or 0) for r in rows}

        # 加上财务手工成本
        rows2 = (
            self.db.query(
                FinancialProjectCost.cost_type,
                func.sum(FinancialProjectCost.amount).label("total"),
            )
            .filter(FinancialProjectCost.project_id == project_id)
            .group_by(FinancialProjectCost.cost_type)
            .all()
        )
        for r in rows2:
            key = r[0] or "其他"
            result[key] = result.get(key, 0) + float(r[1] or 0)

        return result

    def _get_avg_cost_ratio(self, project_ids: List[int]) -> Dict[str, float]:
        """计算一组项目的平均成本类型占比"""
        if not project_ids:
            return {}

        ratios: Dict[str, List[float]] = {}
        for pid in project_ids:
            project = self.db.query(Project).filter(Project.id == pid).first()
            if not project or not project.contract_amount:
                continue
            contract = float(project.contract_amount)
            cost_by_type = self._get_cost_by_type(pid)
            for ct, amount in cost_by_type.items():
                ratio = amount / contract * 100 if contract > 0 else 0
                ratios.setdefault(ct, []).append(ratio)

        return {
            ct: sum(vals) / len(vals) for ct, vals in ratios.items() if vals
        }

    def _get_budget_by_category(self, project_id: int, category: str) -> float:
        """获取项目特定类别的预算金额"""
        result = (
            self.db.query(func.sum(ProjectBudgetItem.budget_amount))
            .join(ProjectBudget, ProjectBudgetItem.budget_id == ProjectBudget.id)
            .filter(
                ProjectBudget.project_id == project_id,
                ProjectBudget.is_active == True,
                ProjectBudgetItem.cost_category == category,
            )
            .scalar()
        )
        return float(result or 0)

    @staticmethod
    def _extract_patterns(projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从高利润项目中提取共同特征"""
        if not projects:
            return {"customer_types": [], "product_types": [], "industries": []}

        # 统计各维度频次
        customer_freq: Dict[str, int] = {}
        product_freq: Dict[str, int] = {}
        industry_freq: Dict[str, int] = {}

        for p in projects:
            c = p.get("customer_name") or "未知"
            customer_freq[c] = customer_freq.get(c, 0) + 1

            pt = p.get("product_category") or p.get("project_type") or "未知"
            product_freq[pt] = product_freq.get(pt, 0) + 1

            ind = p.get("industry") or "未知"
            industry_freq[ind] = industry_freq.get(ind, 0) + 1

        def top_n(freq: Dict[str, int], n: int = 5):
            return [
                {"name": k, "count": v}
                for k, v in sorted(freq.items(), key=lambda x: -x[1])[:n]
            ]

        return {
            "customer_types": top_n(customer_freq),
            "product_types": top_n(product_freq),
            "industries": top_n(industry_freq),
        }
