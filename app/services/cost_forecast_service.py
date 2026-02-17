# -*- coding: utf-8 -*-
"""
成本预测服务

提供成本预测、趋势分析、预警检测等功能
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import (
    CostAlert,
    CostAlertRule,
    CostForecast,
    FinancialProjectCost,
    Machine,
    Project,
    ProjectCost,
)
from app.utils.db_helpers import save_obj


class CostForecastService:
    """成本预测服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # 成本预测算法
    # ========================================================================

    def linear_forecast(
        self,
        project_id: int,
        forecast_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        线性回归预测

        基于历史成本数据进行线性回归，预测完工成本
        """
        if not forecast_date:
            forecast_date = date.today()

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 获取历史成本数据（按月汇总）
        monthly_costs = self._get_monthly_costs(project_id)
        if len(monthly_costs) < 2:
            return {
                "error": "历史数据不足（至少需要2个月数据）",
                "data_points": len(monthly_costs),
            }

        # 转换为DataFrame
        df = pd.DataFrame(monthly_costs)
        df["month_index"] = range(1, len(df) + 1)

        # 线性回归
        from sklearn.linear_model import LinearRegression

        X = df[["month_index"]].values
        y = df["cumulative_cost"].values

        model = LinearRegression()
        model.fit(X, y)

        slope = float(model.coef_[0])
        intercept = float(model.intercept_)

        # 计算R²（拟合优度）
        r_squared = float(model.score(X, y))

        # 预测完工成本
        # 估算总月数（基于项目时间）
        if project.planned_end_date and project.planned_start_date:
            total_months = (
                (project.planned_end_date - project.planned_start_date).days / 30
            )
        else:
            # 假设按当前进度推算
            current_progress = float(project.progress_pct or 0)
            if current_progress > 0:
                total_months = len(monthly_costs) / (current_progress / 100)
            else:
                total_months = len(monthly_costs) * 2  # 默认假设

        total_months = max(total_months, len(monthly_costs))

        forecasted_completion_cost = slope * total_months + intercept

        # 生成月度预测数据
        future_months = int(total_months - len(monthly_costs))
        monthly_forecast_data = []

        for i in range(1, int(total_months) + 1):
            forecasted_cumulative = slope * i + intercept
            if i <= len(monthly_costs):
                # 历史数据
                monthly_forecast_data.append(
                    {
                        "month": monthly_costs[i - 1]["month"],
                        "type": "actual",
                        "monthly_cost": float(monthly_costs[i - 1]["monthly_cost"]),
                        "cumulative_cost": float(
                            monthly_costs[i - 1]["cumulative_cost"]
                        ),
                    }
                )
            else:
                # 预测数据
                month_date = datetime.strptime(
                    monthly_costs[0]["month"], "%Y-%m"
                ) + timedelta(days=30 * (i - 1))
                monthly_cost = (
                    slope if i > 1 else forecasted_cumulative
                )  # 月度增量

                monthly_forecast_data.append(
                    {
                        "month": month_date.strftime("%Y-%m"),
                        "type": "forecast",
                        "monthly_cost": round(monthly_cost, 2),
                        "cumulative_cost": round(forecasted_cumulative, 2),
                    }
                )

        return {
            "method": "LINEAR",
            "forecast_date": forecast_date,
            "forecasted_completion_cost": round(forecasted_completion_cost, 2),
            "current_actual_cost": float(project.actual_cost or 0),
            "current_budget": float(project.budget_amount or 0),
            "current_progress_pct": float(project.progress_pct or 0),
            "data_points": len(monthly_costs),
            "trend_data": {
                "slope": round(slope, 2),
                "intercept": round(intercept, 2),
                "r_squared": round(r_squared, 4),
                "monthly_burn_rate": round(slope, 2),
            },
            "monthly_forecast_data": monthly_forecast_data,
            "is_over_budget": forecasted_completion_cost
            > float(project.budget_amount or 0),
            "budget_variance": round(
                forecasted_completion_cost - float(project.budget_amount or 0), 2
            ),
        }

    def exponential_forecast(
        self,
        project_id: int,
        forecast_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        指数预测

        适用于成本呈指数增长的项目
        """
        if not forecast_date:
            forecast_date = date.today()

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 获取历史成本数据
        monthly_costs = self._get_monthly_costs(project_id)
        if len(monthly_costs) < 2:
            return {"error": "历史数据不足（至少需要2个月数据）"}

        # 计算平均增长率
        growth_rates = []
        for i in range(1, len(monthly_costs)):
            prev_cost = float(monthly_costs[i - 1]["cumulative_cost"])
            curr_cost = float(monthly_costs[i]["cumulative_cost"])
            if prev_cost > 0:
                growth_rate = (curr_cost - prev_cost) / prev_cost
                growth_rates.append(growth_rate)

        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0

        # 预测完工成本
        current_cost = float(monthly_costs[-1]["cumulative_cost"])
        current_progress = float(project.progress_pct or 0)

        if current_progress > 0:
            remaining_progress = 100 - current_progress
            periods_to_complete = remaining_progress / (
                current_progress / len(monthly_costs)
            )
        else:
            periods_to_complete = len(monthly_costs)

        # 指数增长公式: future_cost = current_cost * (1 + growth_rate)^periods
        forecasted_completion_cost = current_cost * (
            (1 + avg_growth_rate) ** periods_to_complete
        )

        # 生成月度预测数据
        monthly_forecast_data = []
        for i, cost_data in enumerate(monthly_costs):
            monthly_forecast_data.append(
                {
                    "month": cost_data["month"],
                    "type": "actual",
                    "monthly_cost": float(cost_data["monthly_cost"]),
                    "cumulative_cost": float(cost_data["cumulative_cost"]),
                }
            )

        # 添加未来预测
        future_months = int(periods_to_complete)
        last_cost = current_cost
        for i in range(1, future_months + 1):
            future_cost = last_cost * (1 + avg_growth_rate)
            month_date = datetime.strptime(
                monthly_costs[-1]["month"], "%Y-%m"
            ) + timedelta(days=30 * i)

            monthly_forecast_data.append(
                {
                    "month": month_date.strftime("%Y-%m"),
                    "type": "forecast",
                    "monthly_cost": round(future_cost - last_cost, 2),
                    "cumulative_cost": round(future_cost, 2),
                }
            )
            last_cost = future_cost

        return {
            "method": "EXPONENTIAL",
            "forecast_date": forecast_date,
            "forecasted_completion_cost": round(forecasted_completion_cost, 2),
            "current_actual_cost": float(project.actual_cost or 0),
            "current_budget": float(project.budget_amount or 0),
            "current_progress_pct": float(project.progress_pct or 0),
            "data_points": len(monthly_costs),
            "trend_data": {
                "avg_growth_rate": round(avg_growth_rate, 4),
                "periods_to_complete": round(periods_to_complete, 2),
            },
            "monthly_forecast_data": monthly_forecast_data,
            "is_over_budget": forecasted_completion_cost
            > float(project.budget_amount or 0),
            "budget_variance": round(
                forecasted_completion_cost - float(project.budget_amount or 0), 2
            ),
        }

    def historical_average_forecast(
        self,
        project_id: int,
        forecast_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        历史平均法预测

        基于历史月均成本预测未来
        """
        if not forecast_date:
            forecast_date = date.today()

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 获取历史成本数据
        monthly_costs = self._get_monthly_costs(project_id)
        if len(monthly_costs) < 1:
            return {"error": "历史数据不足"}

        # 计算月均成本
        total_cost = sum([float(c["monthly_cost"]) for c in monthly_costs])
        avg_monthly_cost = total_cost / len(monthly_costs)

        # 预测完工成本
        current_progress = float(project.progress_pct or 0)
        if current_progress > 0:
            estimated_total_months = len(monthly_costs) / (current_progress / 100)
        else:
            estimated_total_months = len(monthly_costs) * 2

        forecasted_completion_cost = avg_monthly_cost * estimated_total_months

        # 生成月度预测数据
        monthly_forecast_data = []
        cumulative = 0

        # 历史数据
        for cost_data in monthly_costs:
            cumulative += float(cost_data["monthly_cost"])
            monthly_forecast_data.append(
                {
                    "month": cost_data["month"],
                    "type": "actual",
                    "monthly_cost": float(cost_data["monthly_cost"]),
                    "cumulative_cost": round(cumulative, 2),
                }
            )

        # 未来预测
        future_months = int(estimated_total_months - len(monthly_costs))
        for i in range(1, future_months + 1):
            cumulative += avg_monthly_cost
            month_date = datetime.strptime(
                monthly_costs[-1]["month"], "%Y-%m"
            ) + timedelta(days=30 * i)

            monthly_forecast_data.append(
                {
                    "month": month_date.strftime("%Y-%m"),
                    "type": "forecast",
                    "monthly_cost": round(avg_monthly_cost, 2),
                    "cumulative_cost": round(cumulative, 2),
                }
            )

        return {
            "method": "HISTORICAL_AVERAGE",
            "forecast_date": forecast_date,
            "forecasted_completion_cost": round(forecasted_completion_cost, 2),
            "current_actual_cost": float(project.actual_cost or 0),
            "current_budget": float(project.budget_amount or 0),
            "current_progress_pct": float(project.progress_pct or 0),
            "data_points": len(monthly_costs),
            "trend_data": {
                "avg_monthly_cost": round(avg_monthly_cost, 2),
                "estimated_total_months": round(estimated_total_months, 2),
            },
            "monthly_forecast_data": monthly_forecast_data,
            "is_over_budget": forecasted_completion_cost
            > float(project.budget_amount or 0),
            "budget_variance": round(
                forecasted_completion_cost - float(project.budget_amount or 0), 2
            ),
        }

    # ========================================================================
    # 成本趋势分析
    # ========================================================================

    def get_cost_trend(
        self,
        project_id: int,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取成本趋势（月度和累计）

        Args:
            project_id: 项目ID
            start_month: 开始月份（YYYY-MM）
            end_month: 结束月份（YYYY-MM）
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 获取历史成本数据
        monthly_costs = self._get_monthly_costs(project_id, start_month, end_month)

        if not monthly_costs:
            return {
                "project_id": project_id,
                "project_name": project.project_name,
                "monthly_trend": [],
                "cumulative_trend": [],
                "summary": {
                    "total_months": 0,
                    "total_cost": 0,
                    "avg_monthly_cost": 0,
                    "min_monthly_cost": 0,
                    "max_monthly_cost": 0,
                },
            }

        # 计算汇总统计
        monthly_cost_values = [float(c["monthly_cost"]) for c in monthly_costs]
        total_cost = sum(monthly_cost_values)
        avg_monthly_cost = total_cost / len(monthly_costs)

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "monthly_trend": [
                {
                    "month": c["month"],
                    "cost": float(c["monthly_cost"]),
                }
                for c in monthly_costs
            ],
            "cumulative_trend": [
                {
                    "month": c["month"],
                    "cumulative_cost": float(c["cumulative_cost"]),
                }
                for c in monthly_costs
            ],
            "summary": {
                "total_months": len(monthly_costs),
                "total_cost": round(total_cost, 2),
                "avg_monthly_cost": round(avg_monthly_cost, 2),
                "min_monthly_cost": round(min(monthly_cost_values), 2),
                "max_monthly_cost": round(max(monthly_cost_values), 2),
            },
        }

    # ========================================================================
    # 成本燃尽图
    # ========================================================================

    def get_burn_down_data(self, project_id: int) -> Dict[str, Any]:
        """
        获取成本燃尽图数据

        燃尽图显示：
        - 理想燃尽线（基于预算和计划时间）
        - 实际成本线
        - 剩余预算
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        budget = float(project.budget_amount or 0)
        if budget == 0:
            return {"error": "项目预算未设置"}

        # 获取历史成本数据
        monthly_costs = self._get_monthly_costs(project_id)

        # 计算理想燃尽线
        if project.planned_start_date and project.planned_end_date:
            total_months = (
                (project.planned_end_date - project.planned_start_date).days / 30
            )
        else:
            total_months = len(monthly_costs) * 2 if monthly_costs else 12

        # 理想燃尽：每月平均消耗 = 预算 / 总月数
        ideal_monthly_burn = budget / total_months if total_months > 0 else 0

        # 构建燃尽数据
        burn_down_data = []
        remaining_budget = budget

        for i in range(int(total_months) + 1):
            # 理想剩余预算
            ideal_remaining = budget - (ideal_monthly_burn * i)

            # 实际数据
            if i < len(monthly_costs):
                actual_cost = float(monthly_costs[i]["cumulative_cost"])
                actual_remaining = budget - actual_cost
                month = monthly_costs[i]["month"]
            else:
                actual_cost = None
                actual_remaining = None
                # 预测未来月份
                if monthly_costs:
                    month_date = datetime.strptime(
                        monthly_costs[0]["month"], "%Y-%m"
                    ) + timedelta(days=30 * i)
                    month = month_date.strftime("%Y-%m")
                else:
                    month = None

            if month:
                burn_down_data.append(
                    {
                        "month": month,
                        "ideal_remaining": round(max(ideal_remaining, 0), 2),
                        "actual_spent": (
                            round(actual_cost, 2) if actual_cost is not None else None
                        ),
                        "actual_remaining": (
                            round(actual_remaining, 2)
                            if actual_remaining is not None
                            else None
                        ),
                    }
                )

        # 当前状态
        current_spent = float(project.actual_cost or 0)
        remaining = budget - current_spent

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "budget": round(budget, 2),
            "current_spent": round(current_spent, 2),
            "remaining_budget": round(remaining, 2),
            "burn_rate": round(ideal_monthly_burn, 2),
            "burn_down_data": burn_down_data,
            "is_on_track": current_spent
            <= budget * (float(project.progress_pct or 0) / 100),
        }

    # ========================================================================
    # 成本预警检测
    # ========================================================================

    def check_cost_alerts(
        self, project_id: int, auto_create: bool = True
    ) -> List[Dict[str, Any]]:
        """
        检查项目成本预警

        检测：
        1. 超支预警（实际成本 > 预算 × 阈值）
        2. 进度预警（完成度 vs 成本消耗比例）
        3. 趋势预警（成本增长率异常）
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return []

        alerts = []

        # 获取预警规则
        rules = self._get_alert_rules(project_id)

        # 1. 超支预警
        overspend_alert = self._check_overspend_alert(project, rules)
        if overspend_alert:
            alerts.append(overspend_alert)
            if auto_create:
                self._create_alert_record(project_id, overspend_alert)

        # 2. 进度预警
        progress_alert = self._check_progress_mismatch_alert(project, rules)
        if progress_alert:
            alerts.append(progress_alert)
            if auto_create:
                self._create_alert_record(project_id, progress_alert)

        # 3. 趋势预警
        trend_alert = self._check_trend_anomaly_alert(project_id, project, rules)
        if trend_alert:
            alerts.append(trend_alert)
            if auto_create:
                self._create_alert_record(project_id, trend_alert)

        return alerts

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _get_monthly_costs(
        self,
        project_id: int,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取项目月度成本数据（合并ProjectCost和FinancialProjectCost）
        """
        # 查询ProjectCost（业务系统自动产生的成本）
        query1 = (
            self.db.query(
                func.date_format(ProjectCost.cost_date, "%Y-%m").label("month"),
                func.sum(ProjectCost.amount).label("monthly_cost"),
            )
            .filter(ProjectCost.project_id == project_id)
            .filter(ProjectCost.cost_date.isnot(None))
        )

        if start_month:
            query1 = query1.filter(
                func.date_format(ProjectCost.cost_date, "%Y-%m") >= start_month
            )
        if end_month:
            query1 = query1.filter(
                func.date_format(ProjectCost.cost_date, "%Y-%m") <= end_month
            )

        result1 = query1.group_by("month").all()

        # 查询FinancialProjectCost（财务手工录入的成本）
        query2 = (
            self.db.query(
                FinancialProjectCost.cost_month.label("month"),
                func.sum(FinancialProjectCost.amount).label("monthly_cost"),
            )
            .filter(FinancialProjectCost.project_id == project_id)
            .filter(FinancialProjectCost.cost_month.isnot(None))
        )

        if start_month:
            query2 = query2.filter(FinancialProjectCost.cost_month >= start_month)
        if end_month:
            query2 = query2.filter(FinancialProjectCost.cost_month <= end_month)

        result2 = query2.group_by("month").all()

        # 合并两个查询结果
        monthly_dict = {}
        for row in result1:
            month = row.month
            cost = float(row.monthly_cost or 0)
            monthly_dict[month] = monthly_dict.get(month, 0) + cost

        for row in result2:
            month = row.month
            cost = float(row.monthly_cost or 0)
            monthly_dict[month] = monthly_dict.get(month, 0) + cost

        # 排序并计算累计成本
        sorted_months = sorted(monthly_dict.keys())
        cumulative = 0
        result = []

        for month in sorted_months:
            monthly_cost = monthly_dict[month]
            cumulative += monthly_cost
            result.append(
                {
                    "month": month,
                    "monthly_cost": monthly_cost,
                    "cumulative_cost": cumulative,
                }
            )

        return result

    def _get_alert_rules(self, project_id: int) -> Dict[str, Any]:
        """
        获取预警规则（项目特定规则优先于全局规则）
        """
        # 默认规则
        default_rules = {
            "OVERSPEND": {"warning_threshold": 80, "critical_threshold": 100},
            "PROGRESS_MISMATCH": {"deviation_threshold": 15},  # 进度偏差15%
            "TREND_ANOMALY": {"growth_rate_threshold": 0.3},  # 增长率超30%
        }

        # 查询项目特定规则
        project_rules = (
            self.db.query(CostAlertRule)
            .filter(CostAlertRule.project_id == project_id)
            .filter(CostAlertRule.is_enabled == True)  # noqa: E712
            .all()
        )

        # 查询全局规则
        global_rules = (
            self.db.query(CostAlertRule)
            .filter(CostAlertRule.project_id.is_(None))
            .filter(CostAlertRule.is_enabled == True)  # noqa: E712
            .all()
        )

        # 合并规则（项目规则优先）
        rules = default_rules.copy()
        for rule in global_rules + project_rules:
            if rule.rule_config:
                rules[rule.alert_type] = rule.rule_config

        return rules

    def _check_overspend_alert(
        self, project: Project, rules: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """检查超支预警"""
        budget = float(project.budget_amount or 0)
        if budget == 0:
            return None

        actual_cost = float(project.actual_cost or 0)
        consumption_rate = (actual_cost / budget) * 100

        overspend_rule = rules.get("OVERSPEND", {})
        warning_threshold = overspend_rule.get("warning_threshold", 80)
        critical_threshold = overspend_rule.get("critical_threshold", 100)

        if consumption_rate >= critical_threshold:
            level = "CRITICAL"
            message = f"项目成本已超预算！当前成本{actual_cost}元，预算{budget}元"
        elif consumption_rate >= warning_threshold:
            level = "WARNING"
            message = f"项目成本接近预算！当前成本{actual_cost}元，已使用{consumption_rate:.1f}%预算"
        else:
            return None

        return {
            "alert_type": "OVERSPEND",
            "alert_level": level,
            "alert_title": "成本超支预警",
            "alert_message": message,
            "alert_data": {
                "budget": budget,
                "actual_cost": actual_cost,
                "consumption_rate": round(consumption_rate, 2),
                "threshold": warning_threshold
                if level == "WARNING"
                else critical_threshold,
            },
        }

    def _check_progress_mismatch_alert(
        self, project: Project, rules: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """检查进度预警（完成度 vs 成本消耗不匹配）"""
        budget = float(project.budget_amount or 0)
        if budget == 0:
            return None

        progress = float(project.progress_pct or 0)
        actual_cost = float(project.actual_cost or 0)
        cost_consumption = (actual_cost / budget) * 100

        # 计算偏差
        deviation = cost_consumption - progress

        mismatch_rule = rules.get("PROGRESS_MISMATCH", {})
        deviation_threshold = mismatch_rule.get("deviation_threshold", 15)

        if abs(deviation) >= deviation_threshold:
            if deviation > 0:
                # 成本消耗超前
                level = "WARNING"
                message = f"成本消耗超前进度！完成进度{progress}%，成本消耗{cost_consumption:.1f}%，偏差{deviation:.1f}%"
            else:
                # 进度超前成本（可能是好事，但也要提醒）
                level = "INFO"
                message = f"进度超前成本消耗。完成进度{progress}%，成本消耗{cost_consumption:.1f}%"

            return {
                "alert_type": "PROGRESS_MISMATCH",
                "alert_level": level,
                "alert_title": "进度与成本不匹配",
                "alert_message": message,
                "alert_data": {
                    "progress": progress,
                    "cost_consumption": round(cost_consumption, 2),
                    "deviation": round(deviation, 2),
                    "threshold": deviation_threshold,
                },
            }

        return None

    def _check_trend_anomaly_alert(
        self, project_id: int, project: Project, rules: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """检查趋势异常预警（成本增长率异常）"""
        monthly_costs = self._get_monthly_costs(project_id)
        if len(monthly_costs) < 3:
            return None  # 数据不足

        # 计算最近3个月的增长率
        recent_costs = monthly_costs[-3:]
        growth_rates = []

        for i in range(1, len(recent_costs)):
            prev = float(recent_costs[i - 1]["monthly_cost"])
            curr = float(recent_costs[i]["monthly_cost"])
            if prev > 0:
                growth_rate = (curr - prev) / prev
                growth_rates.append(growth_rate)

        if not growth_rates:
            return None

        avg_growth_rate = sum(growth_rates) / len(growth_rates)

        trend_rule = rules.get("TREND_ANOMALY", {})
        threshold = trend_rule.get("growth_rate_threshold", 0.3)

        if avg_growth_rate >= threshold:
            return {
                "alert_type": "TREND_ANOMALY",
                "alert_level": "WARNING",
                "alert_title": "成本增长率异常",
                "alert_message": f"最近3个月平均成本增长率{avg_growth_rate*100:.1f}%，超过阈值{threshold*100}%",
                "alert_data": {
                    "avg_growth_rate": round(avg_growth_rate, 4),
                    "threshold": threshold,
                    "recent_months": [c["month"] for c in recent_costs],
                },
            }

        return None

    def _create_alert_record(
        self, project_id: int, alert_data: Dict[str, Any]
    ) -> None:
        """创建预警记录"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        # 检查是否已存在相同的活动预警
        existing = (
            self.db.query(CostAlert)
            .filter(CostAlert.project_id == project_id)
            .filter(CostAlert.alert_type == alert_data["alert_type"])
            .filter(CostAlert.status == "ACTIVE")
            .first()
        )

        if existing:
            # 更新现有预警
            existing.alert_level = alert_data["alert_level"]
            existing.alert_message = alert_data["alert_message"]
            existing.alert_data = alert_data.get("alert_data")
            existing.updated_at = datetime.now()
        else:
            # 创建新预警
            alert = CostAlert(
                project_id=project_id,
                project_code=project.project_code,
                project_name=project.project_name,
                alert_type=alert_data["alert_type"],
                alert_level=alert_data["alert_level"],
                alert_date=date.today(),
                alert_month=date.today().strftime("%Y-%m"),
                alert_title=alert_data["alert_title"],
                alert_message=alert_data["alert_message"],
                alert_data=alert_data.get("alert_data"),
                current_cost=float(project.actual_cost or 0),
                budget_amount=float(project.budget_amount or 0),
                current_progress=float(project.progress_pct or 0),
                status="ACTIVE",
            )
            self.db.add(alert)

        self.db.commit()

    def save_forecast(
        self, project_id: int, forecast_result: Dict[str, Any], created_by: int
    ) -> CostForecast:
        """保存预测结果到数据库"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")

        forecast = CostForecast(
            project_id=project_id,
            project_code=project.project_code,
            project_name=project.project_name,
            forecast_method=forecast_result["method"],
            forecast_date=forecast_result["forecast_date"],
            forecast_month=forecast_result["forecast_date"].strftime("%Y-%m"),
            forecasted_completion_cost=Decimal(
                str(forecast_result["forecasted_completion_cost"])
            ),
            current_progress_pct=Decimal(
                str(forecast_result.get("current_progress_pct", 0))
            ),
            current_actual_cost=Decimal(
                str(forecast_result.get("current_actual_cost", 0))
            ),
            current_budget=Decimal(str(forecast_result.get("current_budget", 0))),
            monthly_forecast_data=forecast_result.get("monthly_forecast_data"),
            trend_data=forecast_result.get("trend_data"),
            created_by=created_by,
        )

        save_obj(self.db, forecast)

        return forecast
