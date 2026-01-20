# -*- coding: utf-8 -*-
"""
评分辅助方法模块
提供各种评分计算的具体实现
"""

from datetime import date
from typing import Optional

from app.models.project import Customer, Project
from app.models.sales import Lead, Opportunity


class ScoringHelpersMixin:
    """评分辅助方法功能混入类"""

    def _calculate_customer_importance(self, lead: Lead) -> int:
        """计算客户重要性分数"""
        # 通过线索关联的商机查找客户
        if lead.opportunities:
            customer_id = lead.opportunities[0].customer_id
            customer = (
                self.db.query(Customer).filter(Customer.id == customer_id).first()
            )
            return self._get_customer_score(customer)

        # 如果没有商机，尝试通过客户名称查找
        if lead.customer_name:
            customer = (
                self.db.query(Customer)
                .filter(Customer.customer_name == lead.customer_name)
                .first()
            )
            return self._get_customer_score(customer)

        return 5  # 默认分数

    def _get_customer_score(self, customer: Optional[Customer]) -> int:
        """获取客户分数"""
        if not customer:
            return 5

        # 使用credit_level作为客户等级
        level = customer.credit_level or "C"
        level = level.upper()
        return self.CUSTOMER_IMPORTANCE_SCORES.get(level, 10)

    def _calculate_contract_amount_score(self, lead: Lead) -> int:
        """计算预估合同金额分数"""
        # 通过关联的商机获取预估金额
        if lead.opportunities:
            for opp in lead.opportunities:
                if opp.est_amount:
                    return self._get_amount_score(float(opp.est_amount))

        return 5  # 默认分数

    def _get_amount_score(self, amount: float) -> int:
        """根据金额获取分数"""
        for threshold, score in self.CONTRACT_AMOUNT_SCORES:
            if amount >= threshold:
                return score
        return 5

    def _calculate_win_rate_score(self, lead: Lead) -> int:
        """计算中标概率分数"""
        # 通过技术评估获取预测中标率
        if lead.assessment:
            # 如果有评估，使用评估分数
            if (
                hasattr(lead.assessment, "predicted_win_rate")
                and lead.assessment.predicted_win_rate
            ):
                win_rate = float(lead.assessment.predicted_win_rate)
                return self._get_win_rate_score(win_rate)

        # 通过关联的项目获取预测中标率
        if lead.opportunities:
            for opp in lead.opportunities:
                # 查找关联的项目
                projects = (
                    self.db.query(Project)
                    .filter(Project.opportunity_id == opp.id)
                    .all()
                )
                for project in projects:
                    if project.predicted_win_rate:
                        win_rate = float(project.predicted_win_rate)
                        return self._get_win_rate_score(win_rate)

        return 10  # 默认分数（中等概率）

    def _get_win_rate_score(self, win_rate: float) -> int:
        """根据中标概率获取分数"""
        for threshold, score in self.WIN_RATE_SCORES:
            if win_rate >= threshold:
                return score
        return 5

    def _calculate_requirement_maturity_score(self, lead: Lead) -> int:
        """计算需求成熟度分数"""
        # 通过completeness字段判断
        completeness = lead.completeness or 0
        if completeness >= 80:
            return 15
        elif completeness >= 60:
            return 12
        elif completeness >= 40:
            return 8
        elif completeness >= 20:
            return 5
        else:
            return 3

    def _calculate_urgency_score(self, lead: Lead) -> int:
        """计算紧急程度分数"""
        # 通过next_action_at判断
        if lead.next_action_at:
            days_until = (lead.next_action_at.date() - date.today()).days
            if days_until <= 3:
                return 10  # 紧急
            elif days_until <= 7:
                return 7  # 正常
            else:
                return 3  # 不紧急

        return 7  # 默认正常

    def _calculate_opportunity_urgency(self, opportunity: Opportunity) -> int:
        """计算商机紧急程度"""
        # 通过delivery_window判断
        if opportunity.delivery_window:
            # 简单判断：如果包含"紧急"、"急"等关键词
            if (
                "紧急" in opportunity.delivery_window
                or "急" in opportunity.delivery_window
            ):
                return 10
            elif (
                "正常" in opportunity.delivery_window
                or "常规" in opportunity.delivery_window
            ):
                return 7
            else:
                return 3

        return 7  # 默认正常

    def _calculate_relationship_score(self, lead: Lead) -> int:
        """计算客户关系分数"""
        # 判断是否老客户
        if lead.customer_name:
            customer = (
                self.db.query(Customer)
                .filter(Customer.customer_name == lead.customer_name)
                .first()
            )

            if customer:
                # 查询该客户的历史项目数
                project_count = (
                    self.db.query(Project)
                    .join(Customer)
                    .filter(Customer.id == customer.id, Project.outcome == "WON")
                    .count()
                )

                if project_count > 0:
                    return 10  # 老客户/关系好
                else:
                    return 5  # 新客户/关系一般

        return 5  # 默认分数

    def _calculate_opportunity_relationship(
        self, opportunity: Opportunity, customer: Optional[Customer]
    ) -> int:
        """计算商机客户关系分数"""
        if customer:
            # 查询该客户的历史项目数
            project_count = (
                self.db.query(Project)
                .filter(Project.customer_id == customer.id, Project.outcome == "WON")
                .count()
            )

            if project_count >= 3:
                return 10  # 老客户/关系好
            elif project_count >= 1:
                return 7  # 老客户/关系一般
            else:
                return 5  # 新客户/关系一般

        return 5  # 默认分数
