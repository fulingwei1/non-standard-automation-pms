# -*- coding: utf-8 -*-
"""
工时成本自动计算服务
负责从工时记录自动计算项目人工成本
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.timesheet import Timesheet
from app.models.project import ProjectCost, Project
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
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "success": False,
                "message": "项目不存在"
            }
        
        # 查询已审批的工时记录
        query = db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.status == "APPROVED"
        )
        
        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)
        
        timesheets = query.all()
        
        if not timesheets:
            return {
                "success": True,
                "message": "没有已审批的工时记录",
                "cost_count": 0,
                "total_cost": 0
            }
        
        # 如果重新计算，删除现有的工时成本记录
        if recalculate:
            existing_costs = db.query(ProjectCost).filter(
                ProjectCost.project_id == project_id,
                ProjectCost.source_module == "TIMESHEET",
                ProjectCost.source_type == "LABOR_COST"
            ).all()
            
            for cost in existing_costs:
                # 更新项目实际成本
                project.actual_cost = max(0, (project.actual_cost or 0) - float(cost.amount))
                db.delete(cost)
        
        # 按用户和日期分组计算成本
        user_costs: Dict[int, Dict] = {}
        
        for ts in timesheets:
            user_id = ts.user_id
            if user_id not in user_costs:
                user_costs[user_id] = {
                    "user_id": user_id,
                    "user_name": ts.user_name,
                    "total_hours": Decimal("0"),
                    "timesheet_ids": [],
                    "cost_amount": Decimal("0"),
                    "work_date": ts.work_date  # 保存工作日期用于获取时薪
                }
            
            hours = Decimal(str(ts.hours or 0))
            user_costs[user_id]["total_hours"] += hours
            user_costs[user_id]["timesheet_ids"].append(ts.id)
            # 更新工作日期（使用最新的日期）
            if ts.work_date:
                user_costs[user_id]["work_date"] = ts.work_date
        
        # 为每个用户创建成本记录
        created_costs = []
        total_cost = Decimal("0")
        
        for user_id, user_data in user_costs.items():
            # 获取用户时薪（使用工作日期）
            work_date = user_data.get("work_date") or end_date or date.today()
            hourly_rate = LaborCostService.get_user_hourly_rate(db, user_id, work_date)
            
            # 计算成本金额
            cost_amount = user_data["total_hours"] * hourly_rate
            
            # 检查是否已存在该用户的成本记录（在指定日期范围内）
            existing_cost = None
            if not recalculate:
                existing_cost = db.query(ProjectCost).filter(
                    ProjectCost.project_id == project_id,
                    ProjectCost.source_module == "TIMESHEET",
                    ProjectCost.source_type == "LABOR_COST",
                    ProjectCost.source_id == user_id
                ).first()
            
            if existing_cost:
                # 更新现有成本记录
                old_amount = existing_cost.amount
                existing_cost.amount = cost_amount
                existing_cost.cost_date = end_date or date.today()
                existing_cost.description = f"人工成本：{user_data['user_name']}，工时：{user_data['total_hours']}小时"
                
                # 更新项目实际成本
                project.actual_cost = (project.actual_cost or 0) - float(old_amount) + float(cost_amount)
                
                db.add(existing_cost)
                created_costs.append(existing_cost)
                
                # 检查预算执行情况并生成预警
                try:
                    from app.services.cost_alert_service import CostAlertService
                    CostAlertService.check_budget_execution(
                        db, project_id, trigger_source="TIMESHEET", source_id=user_id
                    )
                except Exception as e:
                    # 预警失败不影响成本计算
                    import logging
                    logging.warning(f"成本预警检查失败：{str(e)}")
            else:
                # 创建新的成本记录
                cost = ProjectCost(
                    project_id=project_id,
                    cost_type="LABOR",  # 人工成本
                    cost_category="LABOR",  # 人工
                    source_module="TIMESHEET",
                    source_type="LABOR_COST",
                    source_id=user_id,  # 使用用户ID作为source_id
                    source_no=f"LABOR-{user_id}-{date.today().strftime('%Y%m%d')}",
                    amount=cost_amount,
                    tax_amount=Decimal("0"),  # 人工成本通常不含税
                    cost_date=end_date or date.today(),
                    description=f"人工成本：{user_data['user_name']}，工时：{user_data['total_hours']}小时",
                    created_by=None  # 系统自动创建
                )
                db.add(cost)
                created_costs.append(cost)
                
                # 更新项目实际成本
                project.actual_cost = (project.actual_cost or 0) + float(cost_amount)
                
                # 检查预算执行情况并生成预警
                try:
                    from app.services.cost_alert_service import CostAlertService
                    CostAlertService.check_budget_execution(
                        db, project_id, trigger_source="TIMESHEET", source_id=user_id
                    )
                except Exception as e:
                    # 预警失败不影响成本计算
                    import logging
                    logging.warning(f"成本预警检查失败：{str(e)}")
            
            total_cost += cost_amount
        
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

