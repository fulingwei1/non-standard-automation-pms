# -*- coding: utf-8 -*-
"""
部门报表数据生成器

统一的部门周报、月报数据生成逻辑
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project import Project, ProjectMember
from app.models.timesheet import Timesheet
from app.models.user import User


class DeptReportGenerator:
    """部门报表数据生成器"""

    @staticmethod
    def generate_weekly(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        生成部门周报数据

        Args:
            db: 数据库会话
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据字典
        """
        department = (
            db.query(Department).filter(Department.id == department_id).first()
        )
        if not department:
            return {"error": "部门不存在", "department_id": department_id}

        # 获取部门人员
        dept_members = DeptReportGenerator._get_department_members(db, department)
        dept_user_ids = [u.id for u in dept_members]

        # 基础信息
        summary = {
            "department_id": department.id,
            "department_name": getattr(department, "dept_name", department.name if hasattr(department, "name") else ""),
            "department_code": getattr(department, "dept_code", ""),
            "member_count": len(dept_members),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        }

        # 工时统计
        timesheet_data = DeptReportGenerator._get_timesheet_summary(
            db, dept_user_ids, start_date, end_date
        )

        # 项目工时分布
        project_breakdown = DeptReportGenerator._get_project_breakdown(
            db, dept_user_ids, start_date, end_date
        )

        # 人员负荷
        workload = DeptReportGenerator._get_member_workload(
            db, dept_members, start_date, end_date
        )

        return {
            "summary": summary,
            "members": {
                "total_count": len(dept_members),
                "active_count": len(dept_members),
            },
            "timesheet": {
                "total_hours": timesheet_data["total_hours"],
                "project_breakdown": project_breakdown,
            },
            "workload": workload,
        }

    @staticmethod
    def generate_monthly(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        生成部门月报数据

        Args:
            db: 数据库会话
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据字典
        """
        department = (
            db.query(Department).filter(Department.id == department_id).first()
        )
        if not department:
            return {"error": "部门不存在", "department_id": department_id}

        # 获取部门人员
        dept_members = DeptReportGenerator._get_department_members(db, department)
        dept_user_ids = [u.id for u in dept_members]

        # 基础信息
        summary = {
            "department_id": department.id,
            "department_name": getattr(department, "dept_name", department.name if hasattr(department, "name") else ""),
            "department_code": getattr(department, "dept_code", ""),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "report_type": "月报",
        }

        # 项目统计
        project_stats = DeptReportGenerator._get_project_stats(
            db, dept_user_ids, start_date, end_date
        )

        # 工时统计
        total_days = (end_date - start_date).days + 1
        working_days = total_days * 5 // 7  # 估算工作日

        timesheet_data = DeptReportGenerator._get_timesheet_summary(
            db, dept_user_ids, start_date, end_date
        )

        project_breakdown = DeptReportGenerator._get_project_breakdown(
            db, dept_user_ids, start_date, end_date, limit=15
        )

        # 人员工时详情
        member_workload = DeptReportGenerator._get_member_workload_detailed(
            db, dept_members, start_date, end_date, working_days
        )

        # 关键指标
        avg_utilization = (
            sum(m["utilization_rate"] for m in member_workload) / len(member_workload)
            if member_workload
            else 0
        )

        key_metrics = {
            "total_members": len(dept_members),
            "total_hours": timesheet_data["total_hours"],
            "avg_hours_per_member": (
                round(timesheet_data["total_hours"] / len(dept_members), 2)
                if dept_members
                else 0
            ),
            "avg_utilization_rate": round(avg_utilization, 1),
            "projects_involved": project_stats["total"],
            "high_risk_projects": project_stats["by_health"].get("H3", 0),
        }

        return {
            "summary": summary,
            "key_metrics": key_metrics,
            "project_stats": project_stats,
            "timesheet": {
                "total_hours": timesheet_data["total_hours"],
                "working_days": working_days,
                "project_breakdown": project_breakdown,
            },
            "member_workload": member_workload,
        }

    @staticmethod
    def _get_department_members(
        db: Session, department: Department
    ) -> List[User]:
        """获取部门成员"""
        # 尝试通过 department_id 查询
        members = (
            db.query(User)
            .filter(
                User.department_id == department.id,
                User.is_active == True,
            )
            .all()
        )

        # 如果没有结果，尝试通过部门名称查询
        if not members:
            dept_name = getattr(department, "dept_name", getattr(department, "name", ""))
            if dept_name:
                members = (
                    db.query(User)
                    .filter(
                        User.department == dept_name,
                        User.is_active == True,
                    )
                    .all()
                )

        return members

    @staticmethod
    def _get_timesheet_summary(
        db: Session,
        user_ids: List[int],
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """获取工时汇总"""
        if not user_ids:
            return {"total_hours": 0, "timesheet_count": 0}

        timesheets = (
            db.query(Timesheet)
            .filter(
                Timesheet.user_id.in_(user_ids),
                Timesheet.work_date.between(start_date, end_date),
            )
            .all()
        )

        total_hours = sum(float(t.hours or 0) for t in timesheets)

        return {
            "total_hours": round(total_hours, 2),
            "timesheet_count": len(timesheets),
        }

    @staticmethod
    def _get_project_breakdown(
        db: Session,
        user_ids: List[int],
        start_date: date,
        end_date: date,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取项目工时分布"""
        if not user_ids:
            return []

        timesheets = (
            db.query(Timesheet)
            .filter(
                Timesheet.user_id.in_(user_ids),
                Timesheet.work_date.between(start_date, end_date),
            )
            .all()
        )

        # 按项目统计
        project_hours = {}
        total_hours = 0
        for ts in timesheets:
            key = ts.project_id or 0
            if key not in project_hours:
                project_hours[key] = {"hours": 0, "count": 0}
            hours = float(ts.hours or 0)
            project_hours[key]["hours"] += hours
            project_hours[key]["count"] += 1
            total_hours += hours

        # 转换为列表
        result = []
        for proj_id, data in sorted(
            project_hours.items(), key=lambda x: x[1]["hours"], reverse=True
        )[:limit]:
            if proj_id == 0:
                proj_name = "非项目工作"
            else:
                proj = db.query(Project).filter(Project.id == proj_id).first()
                proj_name = proj.project_name if proj else "未知项目"

            result.append(
                {
                    "project_id": proj_id,
                    "project_name": proj_name,
                    "hours": round(data["hours"], 2),
                    "timesheet_count": data["count"],
                    "percentage": (
                        round(data["hours"] / total_hours * 100, 1)
                        if total_hours > 0
                        else 0
                    ),
                }
            )

        return result

    @staticmethod
    def _get_member_workload(
        db: Session,
        members: List[User],
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """获取成员工作负荷"""
        user_ids = [u.id for u in members]
        if not user_ids:
            return []

        timesheets = (
            db.query(Timesheet)
            .filter(
                Timesheet.user_id.in_(user_ids),
                Timesheet.work_date.between(start_date, end_date),
            )
            .all()
        )

        result = []
        for user in members:
            user_timesheets = [t for t in timesheets if t.user_id == user.id]
            user_hours = sum(float(t.hours or 0) for t in user_timesheets)

            result.append(
                {
                    "user_id": user.id,
                    "user_name": user.real_name or user.username,
                    "position": getattr(user, "position", "") or "",
                    "total_hours": round(user_hours, 2),
                    "avg_daily_hours": round(user_hours / 5, 2),  # 假设每周5天
                }
            )

        return result

    @staticmethod
    def _get_member_workload_detailed(
        db: Session,
        members: List[User],
        start_date: date,
        end_date: date,
        working_days: int,
    ) -> List[Dict[str, Any]]:
        """获取成员工作负荷详情"""
        user_ids = [u.id for u in members]
        if not user_ids:
            return []

        timesheets = (
            db.query(Timesheet)
            .filter(
                Timesheet.user_id.in_(user_ids),
                Timesheet.work_date.between(start_date, end_date),
            )
            .all()
        )

        result = []
        for user in members:
            user_timesheets = [t for t in timesheets if t.user_id == user.id]
            user_hours = sum(float(t.hours or 0) for t in user_timesheets)
            expected_hours = working_days * 8
            utilization = (
                round(user_hours / expected_hours * 100, 1)
                if expected_hours > 0
                else 0
            )

            result.append(
                {
                    "user_id": user.id,
                    "user_name": user.real_name or user.username,
                    "position": getattr(user, "position", "") or "",
                    "total_hours": round(user_hours, 2),
                    "expected_hours": expected_hours,
                    "utilization_rate": utilization,
                    "timesheet_days": len(set(t.work_date for t in user_timesheets)),
                }
            )

        # 按工时排序
        result.sort(key=lambda x: x["total_hours"], reverse=True)
        return result

    @staticmethod
    def _get_project_stats(
        db: Session,
        user_ids: List[int],
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """获取项目统计"""
        if not user_ids:
            return {
                "total": 0,
                "by_stage": {},
                "by_health": {},
                "completed_this_month": 0,
                "started_this_month": 0,
            }

        # 获取部门参与的项目
        project_memberships = (
            db.query(ProjectMember)
            .filter(ProjectMember.user_id.in_(user_ids))
            .all()
        )
        project_ids = list(set(pm.project_id for pm in project_memberships))

        projects = (
            db.query(Project)
            .filter(
                Project.id.in_(project_ids),
                Project.is_active == True,
            )
            .all()
        )

        stats = {
            "total": len(projects),
            "by_stage": {},
            "by_health": {},
            "completed_this_month": 0,
            "started_this_month": 0,
        }

        for project in projects:
            # 按阶段统计
            stage = getattr(project, "stage", "S1") or "S1"
            stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1

            # 按健康度统计
            health = getattr(project, "health", "H1") or "H1"
            stats["by_health"][health] = stats["by_health"].get(health, 0) + 1

            # 本月完成的项目
            if stage == "S9" and project.updated_at:
                if start_date <= project.updated_at.date() <= end_date:
                    stats["completed_this_month"] += 1

            # 本月新开的项目
            if project.created_at:
                if start_date <= project.created_at.date() <= end_date:
                    stats["started_this_month"] += 1

        return stats
