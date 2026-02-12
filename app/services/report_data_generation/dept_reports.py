# -*- coding: utf-8 -*-
"""
部门报表生成（部门周报、部门月报）
"""

from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project import Project, ProjectMember
from app.models.timesheet import Timesheet
from app.models.user import User


class DeptReportMixin:
    """部门报表生成功能混入类"""

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
            "department_name": department.dept_name,
            "department_code": department.dept_code if hasattr(department, 'dept_code') else "",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

        # 获取部门人员
        dept_members = db.query(User).filter(
            User.department == department.dept_name,
            User.is_active
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
    def generate_dept_monthly_report(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成部门月报数据

        Args:
            db: 数据库会话
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据，包含部门概况、项目进展、人员工时、关键指标等
        """
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return {"error": "部门不存在"}

        # 部门基本信息
        summary = {
            "department_name": department.dept_name,
            "department_code": department.dept_code if hasattr(department, 'dept_code') else "",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "report_type": "月报"
        }

        # 获取部门人员（User 模型只有 department 字符串字段）
        dept_members = db.query(User).filter(
            User.department == department.dept_name,
            User.is_active
        ).all()
        dept_user_ids = [u.id for u in dept_members]

        # 1. 部门项目统计
        # 获取部门参与的项目
        project_memberships = db.query(ProjectMember).filter(
            ProjectMember.user_id.in_(dept_user_ids)
        ).all()
        project_ids = list(set(pm.project_id for pm in project_memberships))

        projects = db.query(Project).filter(
            Project.id.in_(project_ids),
            Project.is_active
        ).all()

        # 项目状态统计
        project_stats = {
            "total": len(projects),
            "by_stage": {},
            "by_health": {},
            "completed_this_month": 0,
            "started_this_month": 0
        }

        for project in projects:
            # 按阶段统计
            stage = project.stage or "S1"
            if stage not in project_stats["by_stage"]:
                project_stats["by_stage"][stage] = 0
            project_stats["by_stage"][stage] += 1

            # 按健康度统计
            health = project.health or "H1"
            if health not in project_stats["by_health"]:
                project_stats["by_health"][health] = 0
            project_stats["by_health"][health] += 1

            # 本月完成的项目
            if project.stage == "S9" and project.updated_at:
                if start_date <= project.updated_at.date() <= end_date:
                    project_stats["completed_this_month"] += 1

            # 本月新开的项目
            if project.created_at:
                if start_date <= project.created_at.date() <= end_date:
                    project_stats["started_this_month"] += 1

        # 2. 工时统计
        timesheets = db.query(Timesheet).filter(
            Timesheet.user_id.in_(dept_user_ids),
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)
        total_days = (end_date - start_date).days + 1
        working_days = total_days * 5 // 7  # 估算工作日

        # 按项目统计工时
        project_hours = {}
        for ts in timesheets:
            key = ts.project_id or 0
            if key not in project_hours:
                project_hours[key] = {"hours": 0, "count": 0}
            project_hours[key]["hours"] += float(ts.hours or 0)
            project_hours[key]["count"] += 1

        project_breakdown = []
        for proj_id, data in sorted(project_hours.items(), key=lambda x: x[1]["hours"], reverse=True)[:15]:
            if proj_id == 0:
                proj_name = "非项目工作"
            else:
                proj = db.query(Project).filter(Project.id == proj_id).first()
                proj_name = proj.project_name if proj else "未知项目"
            project_breakdown.append({
                "project_id": proj_id,
                "project_name": proj_name,
                "hours": round(data["hours"], 2),
                "percentage": round(data["hours"] / total_hours * 100, 1) if total_hours > 0 else 0
            })

        # 3. 人员工时详情
        member_workload = []
        for user in dept_members:
            user_timesheets = [t for t in timesheets if t.user_id == user.id]
            user_hours = sum(float(t.hours or 0) for t in user_timesheets)
            expected_hours = working_days * 8  # 每天8小时
            utilization = round(user_hours / expected_hours * 100, 1) if expected_hours > 0 else 0

            member_workload.append({
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "position": getattr(user, 'position', '') or "",
                "total_hours": round(user_hours, 2),
                "expected_hours": expected_hours,
                "utilization_rate": utilization,
                "timesheet_days": len(set(t.work_date for t in user_timesheets))
            })

        # 按工时排序
        member_workload.sort(key=lambda x: x["total_hours"], reverse=True)

        # 4. 关键指标汇总
        avg_utilization = sum(m["utilization_rate"] for m in member_workload) / len(member_workload) if member_workload else 0

        key_metrics = {
            "total_members": len(dept_members),
            "total_hours": round(total_hours, 2),
            "avg_hours_per_member": round(total_hours / len(dept_members), 2) if dept_members else 0,
            "avg_utilization_rate": round(avg_utilization, 1),
            "projects_involved": len(project_ids),
            "high_risk_projects": project_stats["by_health"].get("H3", 0)
        }

        return {
            "summary": summary,
            "key_metrics": key_metrics,
            "project_stats": project_stats,
            "timesheet": {
                "total_hours": round(total_hours, 2),
                "working_days": working_days,
                "project_breakdown": project_breakdown
            },
            "member_workload": member_workload
        }
