# -*- coding: utf-8 -*-
"""
报表数据生成服务
支持多种报表类型的数据生成、角色视角过滤、权限检查
"""

from datetime import date, datetime, timedelta
from typing import Any, List, Optional, Dict
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case

from app.models.project import Project, Machine, ProjectMilestone, ProjectStage, ProjectMember
from app.models.rd_project import RdProject, RdCost
from app.models.timesheet import Timesheet
from app.models.sales import Contract, Opportunity
from app.models.outsourcing import OutsourcingOrder
from app.models.user import User, Role
from app.models.organization import Department


class ReportDataGenerationService:
    """报表数据生成服务"""

    # 角色-报表权限矩阵
    ROLE_REPORT_MATRIX = {
        "PROJECT_MANAGER": ["PROJECT_WEEKLY", "PROJECT_MONTHLY", "COST_ANALYSIS", "RISK_REPORT"],
        "DEPARTMENT_MANAGER": ["DEPT_WEEKLY", "DEPT_MONTHLY", "WORKLOAD_ANALYSIS"],
        "ADMINISTRATIVE_MANAGER": ["COMPANY_MONTHLY", "DEPT_MONTHLY", "WORKLOAD_ANALYSIS"],
        "HR_MANAGER": ["WORKLOAD_ANALYSIS", "DEPT_MONTHLY"],
        "FINANCE_MANAGER": ["COST_ANALYSIS", "COMPANY_MONTHLY"],
        "ENGINEER": ["PROJECT_WEEKLY"],
        "SALES_MANAGER": ["SALES_FUNNEL", "CONTRACT_ANALYSIS"],
        "PROCUREMENT_MANAGER": ["PROCUREMENT_ANALYSIS", "MATERIAL_ANALYSIS"],
        "CUSTOM": ["CUSTOM"]
    }

    @staticmethod
    def check_permission(
        db: Session,
        user: User,
        report_type: str,
        role_code: Optional[str] = None
    ) -> bool:
        """
        检查用户是否有权限生成指定类型的报表

        Args:
            db: 数据库会话
            user: 当前用户
            report_type: 报表类型
            role_code: 指定角色代码（用于多角色场景）

        Returns:
            是否有权限
        """
        # 管理员有所有权限
        if user.is_superuser:
            return True

        # 获取用户的角色代码
        user_role_codes = []
        user_roles = db.query(User).filter(User.id == user.id).first()
        if user_roles:
            # 这里假设用户模型有 roles 关系
            for user_role in getattr(user_roles, 'user_roles', []):
                if user_role.role and user_role.role.is_active:
                    user_role_codes.append(user_role.role.role_code)

        # 如果没有角色，不允许
        if not user_role_codes:
            return False

        # 检查角色-报表矩阵
        for role_code in user_role_codes:
            allowed_reports = ReportDataGenerationService.ROLE_REPORT_MATRIX.get(role_code, [])
            if report_type in allowed_reports:
                return True

        return False

    @staticmethod
    def get_allowed_reports(user_role_code: str) -> List[str]:
        """
        获取角色允许生成的报表类型

        Args:
            user_role_code: 用户角色代码

        Returns:
            允许的报表类型列表
        """
        return ReportDataGenerationService.ROLE_REPORT_MATRIX.get(user_role_code, [])

    @staticmethod
    def generate_project_weekly_report(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成项目周报数据

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 获取项目基本信息
        summary = {
            "project_code": project.project_code if hasattr(project, 'project_code') else "",
            "project_name": project.project_name,
            "customer_name": project.customer_name if hasattr(project, 'customer_name') else "",
            "current_stage": project.current_stage if hasattr(project, 'current_stage') else "S1",
            "health_status": project.health_status if hasattr(project, 'health_status') else "H1",
            "progress": float(project.progress or 0),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

        # 获取本周的里程碑完成情况
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.milestone_date.between(start_date, end_date)
        ).all()

        milestone_summary = {
            "total": len(milestones),
            "completed": sum(1 for m in milestones if m.status == "COMPLETED"),
            "delayed": sum(1 for m in milestones if m.status == "DELAYED"),
            "in_progress": sum(1 for m in milestones if m.status == "IN_PROGRESS")
        }

        # 获取工时数据
        timesheets = db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)
        unique_workers = len(set(t.user_id for t in timesheets))

        # 获取机台进度
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        machine_summary = []
        for machine in machines:
            machine_summary.append({
                "machine_code": machine.machine_code if hasattr(machine, 'machine_code') else f"M-{machine.id}",
                "machine_name": machine.machine_name if hasattr(machine, 'machine_name') else f"机台{machine.id}",
                "status": machine.status if hasattr(machine, 'status') else "PENDING",
                "progress": float(machine.progress or 0)
            })

        # 风险提示
        risks = []
        if summary["health_status"] in ["H2", "H3"]:
            risks.append({
                "type": "健康度",
                "level": "HIGH" if summary["health_status"] == "H3" else "MEDIUM",
                "description": f"项目健康度为 {summary['health_status']}"
            })

        if milestone_summary["delayed"] > 0:
            risks.append({
                "type": "里程碑延期",
                "level": "HIGH",
                "description": f"有 {milestone_summary['delayed']} 个里程碑延期"
            })

        return {
            "summary": summary,
            "milestones": {
                "summary": milestone_summary,
                "details": [
                    {
                        "name": m.milestone_name if hasattr(m, 'milestone_name') else f"里程碑{m.id}",
                        "date": m.milestone_date.isoformat() if hasattr(m, 'milestone_date') and m.milestone_date else None,
                        "status": m.status if hasattr(m, 'status') else "PENDING"
                    }
                    for m in milestones
                ]
            },
            "timesheet": {
                "total_hours": round(total_hours, 2),
                "unique_workers": unique_workers,
                "avg_hours_per_worker": round(total_hours / unique_workers, 2) if unique_workers > 0 else 0
            },
            "machines": machine_summary,
            "risks": risks
        }

    @staticmethod
    def generate_project_monthly_report(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成项目月报数据

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 基础信息
        summary = {
            "project_code": project.project_code if hasattr(project, 'project_code') else "",
            "project_name": project.project_name,
            "current_stage": project.current_stage if hasattr(project, 'current_stage') else "S1",
            "health_status": project.health_status if hasattr(project, 'health_status') else "H1",
            "progress": float(project.progress or 0),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

        # 进度趋势（按周统计）
        weeks = []
        current = start_date
        week_num = 1
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project_id,
                Timesheet.work_date.between(current, week_end)
            ).all()
            week_hours = sum(float(t.hours or 0) for t in week_timesheets)

            weeks.append({
                "week": week_num,
                "start": current.isoformat(),
                "end": week_end.isoformat(),
                "hours": round(week_hours, 2)
            })

            current = week_end + timedelta(days=1)
            week_num += 1

        # 里程碑完成情况
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.milestone_date.between(start_date, end_date)
        ).all()

        milestone_details = []
        for m in milestones:
            milestone_details.append({
                "name": m.milestone_name if hasattr(m, 'milestone_name') else f"里程碑{m.id}",
                "planned_date": m.milestone_date.isoformat() if hasattr(m, 'milestone_date') and m.milestone_date else None,
                "actual_date": m.actual_date.isoformat() if hasattr(m, 'actual_date') and m.actual_date else None,
                "status": m.status if hasattr(m, 'status') else "PENDING"
            })

        # 成本概况
        cost_summary = {
            "planned_cost": float(project.budget_amount or 0) if hasattr(project, 'budget_amount') else 0,
            "actual_cost": 0,  # 需要从成本模块获取
            "cost_variance": 0,
            "cost_variance_percent": 0
        }

        return {
            "summary": summary,
            "progress_trend": weeks,
            "milestones": milestone_details,
            "cost": cost_summary
        }

    @staticmethod
    def generate_dept_weekly_report(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成部门周报数据

        Args:
            db: 数据库会话
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return {"error": "部门不存在"}

        # 部门基本信息
        summary = {
            "department_name": department.name,
            "department_code": department.code if hasattr(department, 'code') else "",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

        # 获取部门人员
        dept_members = db.query(User).filter(
            User.department_id == department_id,
            User.is_active == True
        ).all()

        # 部门工时统计
        dept_user_ids = [u.id for u in dept_members]
        timesheets = db.query(Timesheet).filter(
            Timesheet.user_id.in_(dept_user_ids),
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)

        # 按项目统计工时
        project_hours = {}
        for ts in timesheets:
            key = ts.project_id or 0
            if key not in project_hours:
                project_hours[key] = {"hours": 0, "count": 0}
            project_hours[key]["hours"] += float(ts.hours or 0)
            project_hours[key]["count"] += 1

        project_summary = []
        for proj_id, data in sorted(project_hours.items(), key=lambda x: x[1]["hours"], reverse=True)[:10]:
            if proj_id == 0:
                continue
            proj = db.query(Project).filter(Project.id == proj_id).first()
            project_summary.append({
                "project_id": proj_id,
                "project_name": proj.project_name if proj else "未知项目",
                "hours": round(data["hours"], 2),
                "timesheet_count": data["count"]
            })

        # 人员负荷统计
        workload_summary = []
        for user in dept_members:
            user_timesheets = [t for t in timesheets if t.user_id == user.id]
            user_hours = sum(float(t.hours or 0) for t in user_timesheets)
            workload_summary.append({
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "position": user.position if hasattr(user, 'position') else "",
                "total_hours": round(user_hours, 2),
                "avg_daily_hours": round(user_hours / 5, 2)  # 假设每周5天工作
            })

        return {
            "summary": summary,
            "members": {
                "total_count": len(dept_members),
                "active_count": len(dept_members)
            },
            "timesheet": {
                "total_hours": round(total_hours, 2),
                "project_breakdown": project_summary
            },
            "workload": workload_summary
        }

    @staticmethod
    def generate_workload_analysis(
        db: Session,
        department_id: Optional[int] = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        生成负荷分析报告

        Args:
            db: 数据库会话
            department_id: 部门ID（可选）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # 获取人员范围
        if department_id:
            users = db.query(User).filter(
                User.department_id == department_id,
                User.is_active == True
            ).all()
            dept = db.query(Department).filter(Department.id == department_id).first()
            scope_name = dept.name if dept else "部门"
        else:
            users = db.query(User).filter(User.is_active == True).all()
            scope_name = "全公司"

        user_ids = [u.id for u in users]

        # 工时统计
        timesheets = db.query(Timesheet).filter(
            Timesheet.user_id.in_(user_ids),
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        # 按人员统计
        workload_by_user = {}
        for ts in timesheets:
            user_id = ts.user_id
            if user_id not in workload_by_user:
                workload_by_user[user_id] = {
                    "hours": 0,
                    "days": 0,
                    "projects": set()
                }
            workload_by_user[user_id]["hours"] += float(ts.hours or 0)
            if ts.project_id:
                workload_by_user[user_id]["projects"].add(ts.project_id)

        # 转换为列表
        workload_list = []
        for user_id, data in workload_by_user.items():
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue

            hours = data["hours"]
            days = hours / 8  # 假设每天8小时
            project_count = len(data["projects"])

            # 负荷评级
            if days > 22:  # 超过一个月工作日
                load_level = "OVERLOAD"
            elif days > 18:
                load_level = "HIGH"
            elif days > 12:
                load_level = "MEDIUM"
            else:
                load_level = "LOW"

            workload_list.append({
                "user_id": user_id,
                "user_name": user.real_name or user.username,
                "department": user.department if hasattr(user, 'department') else "",
                "total_hours": round(hours, 2),
                "working_days": round(days, 1),
                "project_count": project_count,
                "load_level": load_level
            })

        # 按负荷分组
        load_summary = {
            "OVERLOAD": sum(1 for w in workload_list if w["load_level"] == "OVERLOAD"),
            "HIGH": sum(1 for w in workload_list if w["load_level"] == "HIGH"),
            "MEDIUM": sum(1 for w in workload_list if w["load_level"] == "MEDIUM"),
            "LOW": sum(1 for w in workload_list if w["load_level"] == "LOW")
        }

        return {
            "summary": {
                "scope": scope_name,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_users": len(users),
                "active_users": len(workload_list)
            },
            "load_distribution": load_summary,
            "workload_details": sorted(workload_list, key=lambda x: x["working_days"], reverse=True)
        }

    @staticmethod
    def generate_cost_analysis(
        db: Session,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        生成成本分析报告

        Args:
            db: 数据库会话
            project_id: 项目ID（可选，不指定则汇总所有项目）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        if not start_date:
            start_date = date.today().replace(day=1)  # 本月初
        if not end_date:
            end_date = date.today()

        # 获取项目列表
        if project_id:
            projects = db.query(Project).filter(Project.id == project_id).all()
        else:
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status.in_(["IN_PROGRESS", "ON_HOLD"])
            ).all()

        project_summaries = []
        total_budget = 0
        total_actual = 0

        for project in projects:
            budget = float(project.budget_amount or 0) if hasattr(project, 'budget_amount') else 0
            total_budget += budget

            # 获取项目工时成本
            timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project.id,
                Timesheet.work_date.between(start_date, end_date)
            ).all()
            labor_hours = sum(float(t.hours or 0) for t in timesheets)

            # 估算人工成本（假设平均时薪100元）
            estimated_labor_cost = labor_hours * 100
            total_actual += estimated_labor_cost

            variance = budget - estimated_labor_cost
            variance_percent = (variance / budget * 100) if budget > 0 else 0

            project_summaries.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "budget": round(budget, 2),
                "actual_cost": round(estimated_labor_cost, 2),
                "variance": round(variance, 2),
                "variance_percent": round(variance_percent, 2)
            })

        return {
            "summary": {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "project_count": len(projects),
                "total_budget": round(total_budget, 2),
                "total_actual": round(total_actual, 2),
                "total_variance": round(total_budget - total_actual, 2)
            },
            "project_breakdown": project_summaries
        }

    @staticmethod
    def generate_report_by_type(
        db: Session,
        report_type: str,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        根据报表类型生成数据

        Args:
            db: 数据库会话
            report_type: 报表类型
            project_id: 项目ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        if not start_date:
            start_date = date.today() - timedelta(days=7)
        if not end_date:
            end_date = date.today()

        if report_type == "PROJECT_WEEKLY":
            if not project_id:
                return {"error": "项目周报需要指定项目ID"}
            return ReportDataGenerationService.generate_project_weekly_report(
                db, project_id, start_date, end_date
            )

        elif report_type == "PROJECT_MONTHLY":
            if not project_id:
                return {"error": "项目月报需要指定项目ID"}
            return ReportDataGenerationService.generate_project_monthly_report(
                db, project_id, start_date, end_date
            )

        elif report_type == "DEPT_WEEKLY":
            if not department_id:
                return {"error": "部门周报需要指定部门ID"}
            return ReportDataGenerationService.generate_dept_weekly_report(
                db, department_id, start_date, end_date
            )

        elif report_type == "WORKLOAD_ANALYSIS":
            return ReportDataGenerationService.generate_workload_analysis(
                db, department_id, start_date, end_date
            )

        elif report_type == "COST_ANALYSIS":
            return ReportDataGenerationService.generate_cost_analysis(
                db, project_id, start_date, end_date
            )

        else:
            return {
                "report_type": report_type,
                "summary": {},
                "details": [],
                "charts": [],
                "message": "该报表类型待实现"
            }


# 创建单例
report_data_service = ReportDataGenerationService()
