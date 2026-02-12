"""
问题成本关联服务
用于查询问题关联的成本记录和工时记录
"""
from decimal import Decimal
from typing import Dict

from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.models.project import ProjectCost
from app.models.timesheet import Timesheet


class IssueCostService:
    """问题成本关联服务"""

    @staticmethod
    def get_issue_related_costs(db: Session, issue_no: str) -> Dict:
        """
        获取问题关联的成本记录

        通过问题编号在ProjectCost的description中查找匹配的记录

        Args:
            db: 数据库会话
            issue_no: 问题编号

        Returns:
            dict: 包含库存损失、总成本和成本记录列表
        """
        # 从ProjectCost的description中查找问题编号
        costs_query = db.query(ProjectCost)
        costs_query = apply_keyword_filter(
            costs_query,
            ProjectCost,
            issue_no,
            "description",
            use_ilike=False,
        )
        costs = costs_query.all()

        # 计算库存损失（description中包含"库存"的成本）
        inventory_loss = Decimal(0)
        for cost in costs:
            if cost.description and '库存' in cost.description:
                inventory_loss += cost.amount or Decimal(0)

        # 计算总成本
        total_cost = sum(cost.amount or Decimal(0) for cost in costs)

        return {
            'inventory_loss': inventory_loss,
            'total_cost': total_cost,
            'costs': costs
        }

    @staticmethod
    def get_issue_related_hours(db: Session, issue_no: str) -> Dict:
        """
        获取问题关联的工时记录

        通过问题编号在Timesheet的work_content或work_result中查找匹配的记录

        Args:
            db: 数据库会话
            issue_no: 问题编号

        Returns:
            dict: 包含总工时和工时记录列表
        """
        # 从Timesheet的work_content或work_result中查找问题编号
        timesheets_query = db.query(Timesheet)
        timesheets_query = apply_keyword_filter(
            timesheets_query,
            Timesheet,
            issue_no,
            ["work_content", "work_result"],
            use_ilike=False,
        )
        timesheets = timesheets_query.all()

        # 只计算已审批的工时
        total_hours = Decimal(0)
        approved_timesheets = []
        for ts in timesheets:
            if ts.status == 'APPROVED':
                total_hours += ts.hours or Decimal(0)
                approved_timesheets.append(ts)

        return {
            'total_hours': total_hours,
            'timesheets': approved_timesheets
        }

    @staticmethod
    def get_issue_cost_summary(db: Session, issue_no: str) -> Dict:
        """
        获取问题成本汇总（成本和工时）

        Args:
            db: 数据库会话
            issue_no: 问题编号

        Returns:
            dict: 包含成本和工时的汇总信息
        """
        costs_info = IssueCostService.get_issue_related_costs(db, issue_no)
        hours_info = IssueCostService.get_issue_related_hours(db, issue_no)

        return {
            'issue_no': issue_no,
            'inventory_loss': costs_info['inventory_loss'],
            'total_cost': costs_info['total_cost'],
            'total_hours': hours_info['total_hours'],
            'cost_count': len(costs_info['costs']),
            'timesheet_count': len(hours_info['timesheets'])
        }





