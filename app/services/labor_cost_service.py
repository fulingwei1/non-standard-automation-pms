# -*- coding: utf-8 -*-
"""
工时成本自动计算服务
负责从工时记录自动计算项目人工成本
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost
from app.models.timesheet import Timesheet
from app.models.user import User


class LaborCostService:
    """工时成本自动计算服务"""

    # 默认时薪配置（可以后续从用户配置或系统配置中读取）
    DEFAULT_HOURLY_RATE = Decimal("100")  # 默认100元/小时

    @staticmethod
    def get_user_hourly_rate(db: Session, user_id: int, work_date: Optional[date] = None) -> Decimal:
        """
        获取用户时薪（从时薪配置服务读取）

        Args:
            db: 数据库会话
            user_id: 用户ID
            work_date: 工作日期（可选）

        Returns:
            时薪（元/小时）
        """
        from app.services.hourly_rate_service import HourlyRateService
        return HourlyRateService.get_user_hourly_rate(db, user_id, work_date)

    @staticmethod
    def calculate_project_labor_cost(
        db: Session,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        recalculate: bool = False
    ) -> Dict:
        """
        计算项目人工成本

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            recalculate: 是否重新计算（如果为True，会删除现有记录重新计算）

        Returns:
            计算结果字典，包含创建的成本记录数量、总成本等
        """
        from app.services.labor_cost_calculation_service import (
            delete_existing_costs,
            group_timesheets_by_user,
            process_user_costs,
            query_approved_timesheets,
        )

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "success": False,
                "message": "项目不存在"
            }

        # 查询已审批的工时记录
        timesheets = query_approved_timesheets(db, project_id, start_date, end_date)

        if not timesheets:
            return {
                "success": True,
                "message": "没有已审批的工时记录",
                "cost_count": 0,
                "total_cost": 0
            }

        # 如果重新计算，删除现有的工时成本记录
        if recalculate:
            delete_existing_costs(db, project, project_id)

        # 按用户分组工时记录
        user_costs = group_timesheets_by_user(timesheets)

        # 处理用户成本
        created_costs, total_cost = process_user_costs(
            db, project, project_id, user_costs, end_date, recalculate
        )

        db.add(project)
        db.commit()

        return {
            "success": True,
            "message": f"成功计算{len(created_costs)}条人工成本记录",
            "cost_count": len(created_costs),
            "total_cost": float(total_cost),
            "total_hours": float(sum([user_data["total_hours"] for user_data in user_costs.values()])),
            "user_count": len(user_costs)
        }

    @staticmethod
    def calculate_all_projects_labor_cost(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        批量计算所有项目的人工成本

        Args:
            db: 数据库会话
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            project_ids: 项目ID列表（可选，不提供则计算所有项目）

        Returns:
            批量计算结果
        """
        # 查询有工时记录的项目
        query = db.query(Timesheet.project_id).filter(
            Timesheet.status == "APPROVED"
        ).distinct()

        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)

        if project_ids:
            query = query.filter(Timesheet.project_id.in_(project_ids))

        project_ids_with_timesheets = [row[0] for row in query.all()]

        results = []
        success_count = 0
        fail_count = 0

        for project_id in project_ids_with_timesheets:
            try:
                result = LaborCostService.calculate_project_labor_cost(
                    db, project_id, start_date, end_date, recalculate=True
                )
                results.append({
                    "project_id": project_id,
                    **result
                })
                if result.get("success"):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                results.append({
                    "project_id": project_id,
                    "success": False,
                    "message": str(e)
                })
                fail_count += 1

        return {
            "success": True,
            "message": f"批量计算完成：成功{success_count}个，失败{fail_count}个",
            "total_projects": len(project_ids_with_timesheets),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }

    @staticmethod
    def calculate_monthly_labor_cost(
        db: Session,
        year: int,
        month: int,
        project_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        计算指定月份的项目人工成本

        Args:
            db: 数据库会话
            year: 年份
            month: 月份
            project_ids: 项目ID列表（可选）

        Returns:
            月度计算结果
        """
        # 计算日期范围
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        return LaborCostService.calculate_all_projects_labor_cost(
            db, start_date, end_date, project_ids
        )

