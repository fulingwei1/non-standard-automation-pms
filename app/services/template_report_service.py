# -*- coding: utf-8 -*-
"""
模板报表生成服务
基于报表模板配置动态生成报表数据
"""

from datetime import date, datetime, timedelta
from typing import Any, List, Optional, Dict
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.project import Project, ProjectMilestone, Machine
from app.models.timesheet import Timesheet
from app.models.report_center import ReportTemplate
from app.models.user import User, Department
from app.models.rd_project import RdProject, RdCost


class TemplateReportService:
    """模板报表生成服务"""

    @staticmethod
    def generate_from_template(
        db: Session,
        template: ReportTemplate,
        project_id: Optional[int] = None,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        根据模板配置生成报表数据

        Args:
            db: 数据库会话
            template: 报表模板
            project_id: 项目ID
            department_id: 部门ID
            start_date: 开始日期
            end_date: 结束日期
            filters: 额外过滤条件

        Returns:
            报表数据
        """
        # 设置默认日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 解析模板配置
        sections_config = template.sections or {}
        metrics_config = template.metrics_config or {}

        # 生成报表数据
        report_data = {
            "template_id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "report_type": template.report_type,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "sections": {},
            "metrics": {},
            "charts": []
        }

        # 根据报表类型生成数据
        if template.report_type == "PROJECT_WEEKLY":
            report_data.update(TemplateReportService._generate_project_weekly(
                db, project_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "PROJECT_MONTHLY":
            report_data.update(TemplateReportService._generate_project_monthly(
                db, project_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "DEPT_WEEKLY":
            report_data.update(TemplateReportService._generate_dept_weekly(
                db, department_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "DEPT_MONTHLY":
            report_data.update(TemplateReportService._generate_dept_monthly(
                db, department_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "WORKLOAD_ANALYSIS":
            report_data.update(TemplateReportService._generate_workload_analysis(
                db, department_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "COST_ANALYSIS":
            report_data.update(TemplateReportService._generate_cost_analysis(
                db, project_id, start_date, end_date, sections_config, metrics_config
            ))
        elif template.report_type == "COMPANY_MONTHLY":
            report_data.update(TemplateReportService._generate_company_monthly(
                db, start_date, end_date, sections_config, metrics_config
            ))
        else:
            # 通用报表生成
            report_data.update(TemplateReportService._generate_generic_report(
                db, template.report_type, project_id, department_id, start_date, end_date
            ))

        return report_data

    @staticmethod
    def _generate_project_weekly(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成项目周报"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 基础信息
        summary = {
            "project_code": getattr(project, 'project_code', ''),
            "project_name": project.project_name,
            "customer_name": getattr(project, 'customer_name', ''),
            "current_stage": getattr(project, 'current_stage', 'S1'),
            "health_status": getattr(project, 'health_status', 'H1'),
            "progress": float(project.progress or 0)
        }

        # 里程碑
        milestones_data = []
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.milestone_date.between(start_date, end_date)
        ).all()

        for m in milestones:
            milestones_data.append({
                "name": getattr(m, 'milestone_name', f"里程碑{m.id}"),
                "date": getattr(m, 'milestone_date', None),
                "status": getattr(m, 'status', 'PENDING'),
                "actual_date": getattr(m, 'actual_date', None)
            })

        # 工时统计
        timesheets = db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)
        unique_workers = len(set(t.user_id for t in timesheets))

        # 机台进度
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        machine_data = []
        for m in machines:
            machine_data.append({
                "machine_code": getattr(m, 'machine_code', f"M-{m.id}"),
                "machine_name": getattr(m, 'machine_name', f"机台{m.id}"),
                "status": getattr(m, 'status', 'PENDING'),
                "progress": float(m.progress or 0)
            })

        return {
            "summary": summary,
            "sections": {
                "milestones": {
                    "title": "里程碑完成情况",
                    "type": "table",
                    "data": milestones_data,
                    "summary": {
                        "total": len(milestones),
                        "completed": sum(1 for m in milestones if getattr(m, 'status', '') == 'COMPLETED'),
                        "delayed": sum(1 for m in milestones if getattr(m, 'status', '') == 'DELAYED')
                    }
                },
                "timesheet": {
                    "title": "工时统计",
                    "type": "summary",
                    "data": {
                        "total_hours": round(total_hours, 2),
                        "unique_workers": unique_workers,
                        "avg_hours": round(total_hours / unique_workers, 2) if unique_workers > 0 else 0
                    }
                },
                "machines": {
                    "title": "机台进度",
                    "type": "list",
                    "data": machine_data
                }
            },
            "metrics": {
                "total_hours": round(total_hours, 2),
                "active_workers": unique_workers,
                "milestone_completion_rate": round(
                    sum(1 for m in milestones if getattr(m, 'status', '') == 'COMPLETED') / max(len(milestones), 1) * 100,
                    2
                ) if milestones else 0
            }
        }

    @staticmethod
    def _generate_dept_weekly(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成部门周报"""
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return {"error": "部门不存在"}

        # 部门人员
        users = db.query(User).filter(
            User.department_id == department_id,
            User.is_active == True
        ).all()

        user_ids = [u.id for u in users]

        # 工时统计
        timesheets = db.query(Timesheet).filter(
            Timesheet.user_id.in_(user_ids),
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        total_hours = sum(float(t.hours or 0) for t in timesheets)

        # 按项目统计
        project_stats = {}
        for ts in timesheets:
            pid = ts.project_id or 0
            if pid == 0:
                continue
            if pid not in project_stats:
                project_stats[pid] = {"hours": 0, "count": 0}
            project_stats[pid]["hours"] += float(ts.hours or 0)
            project_stats[pid]["count"] += 1

        project_list = []
        for pid, stats in sorted(project_stats.items(), key=lambda x: x[1]["hours"], reverse=True)[:10]:
            proj = db.query(Project).filter(Project.id == pid).first()
            project_list.append({
                "project_id": pid,
                "project_name": proj.project_name if proj else "未知项目",
                "hours": round(stats["hours"], 2),
                "timesheet_count": stats["count"]
            })

        return {
            "summary": {
                "department_name": department.name,
                "member_count": len(users),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            },
            "sections": {
                "projects": {
                    "title": "项目工时分布",
                    "type": "table",
                    "data": project_list
                },
                "timesheet": {
                    "title": "工时汇总",
                    "type": "summary",
                    "data": {
                        "total_hours": round(total_hours, 2),
                        "avg_hours_per_user": round(total_hours / len(users), 2) if users else 0
                    }
                }
            },
            "metrics": {
                "total_hours": round(total_hours, 2),
                "active_projects": len(project_stats),
                "active_members": len(users)
            }
        }

    @staticmethod
    def _generate_workload_analysis(
        db: Session,
        department_id: Optional[int],
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成负荷分析报表"""
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
        workload_list = []
        overload_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for user in users:
            user_timesheets = [t for t in timesheets if t.user_id == user.id]
            hours = sum(float(t.hours or 0) for t in user_timesheets)
            working_days = hours / 8  # 假设每天8小时

            # 负荷评级
            if working_days > 22:
                load_level = "OVERLOAD"
                overload_count += 1
            elif working_days > 18:
                load_level = "HIGH"
                high_count += 1
            elif working_days > 12:
                load_level = "MEDIUM"
                medium_count += 1
            else:
                load_level = "LOW"
                low_count += 1

            workload_list.append({
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "department": user.department or "",
                "total_hours": round(hours, 2),
                "working_days": round(working_days, 1),
                "load_level": load_level
            })

        # 排序
        workload_list.sort(key=lambda x: x["working_days"], reverse=True)

        return {
            "summary": {
                "scope": scope_name,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_users": len(users)
            },
            "sections": {
                "workload": {
                    "title": "人员负荷详情",
                    "type": "table",
                    "data": workload_list
                }
            },
            "metrics": {
                "overload_count": overload_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count
            },
            "charts": [
                {
                    "type": "pie",
                    "title": "负荷分布",
                    "data": [
                        {"name": "超负荷", "value": overload_count},
                        {"name": "高负荷", "value": high_count},
                        {"name": "中等负荷", "value": medium_count},
                        {"name": "低负荷", "value": low_count}
                    ]
                }
            ]
        }

    @staticmethod
    def _generate_cost_analysis(
        db: Session,
        project_id: Optional[int],
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成成本分析报表"""
        if project_id:
            projects = db.query(Project).filter(Project.id == project_id).all()
        else:
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status.in_(["IN_PROGRESS", "ON_HOLD"])
            ).all()

        project_data = []
        total_budget = 0
        total_actual = 0

        for project in projects:
            budget = float(project.budget_amount or 0) if hasattr(project, 'budget_amount') else 0
            total_budget += budget

            # 获取工时成本
            timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project.id,
                Timesheet.work_date.between(start_date, end_date)
            ).all()

            labor_hours = sum(float(t.hours or 0) for t in timesheets)
            estimated_labor_cost = labor_hours * 100  # 假设时薪100元

            total_actual += estimated_labor_cost

            project_data.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "budget": round(budget, 2),
                "actual_cost": round(estimated_labor_cost, 2),
                "variance": round(budget - estimated_labor_cost, 2),
                "variance_percent": round((budget - estimated_labor_cost) / budget * 100, 2) if budget > 0 else 0
            })

        return {
            "summary": {
                "project_count": len(projects),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            },
            "sections": {
                "cost_breakdown": {
                    "title": "项目成本明细",
                    "type": "table",
                    "data": project_data
                }
            },
            "metrics": {
                "total_budget": round(total_budget, 2),
                "total_actual": round(total_actual, 2),
                "total_variance": round(total_budget - total_actual, 2)
            },
            "charts": [
                {
                    "type": "bar",
                    "title": "预算 vs 实际成本",
                    "x_field": "project_name",
                    "y_fields": ["budget", "actual_cost"]
                }
            ]
        }

    @staticmethod
    def _generate_company_monthly(
        db: Session,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成公司月报"""
        # 获取所有活跃项目
        projects = db.query(Project).filter(
            Project.is_active == True
        ).all()

        # 项目状态统计
        status_counts = {}
        for p in projects:
            status = p.status or "UNKNOWN"
            status_counts[status] = status_counts.get(status, 0) + 1

        # 健康度统计
        health_counts = {}
        for p in projects:
            health = getattr(p, 'health_status', 'H1')
            health_counts[health] = health_counts.get(health, 0) + 1

        # 部门工时
        departments = db.query(Department).all()
        dept_hours = []
        for dept in departments:
            users = db.query(User).filter(
                User.department_id == dept.id,
                User.is_active == True
            ).all()
            user_ids = [u.id for u in users]

            timesheets = db.query(Timesheet).filter(
                Timesheet.user_id.in_(user_ids),
                Timesheet.work_date.between(start_date, end_date)
            ).all()

            total_hours = sum(float(t.hours or 0) for t in timesheets)
            if total_hours > 0:
                dept_hours.append({
                    "department": dept.name,
                    "hours": round(total_hours, 2)
                })

        return {
            "summary": {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_projects": len(projects)
            },
            "sections": {
                "project_status": {
                    "title": "项目状态分布",
                    "type": "summary",
                    "data": status_counts
                },
                "health_status": {
                    "title": "项目健康度分布",
                    "type": "summary",
                    "data": health_counts
                },
                "department_hours": {
                    "title": "部门工时统计",
                    "type": "table",
                    "data": dept_hours
                }
            },
            "metrics": {
                "total_projects": len(projects),
                "active_projects": status_counts.get("IN_PROGRESS", 0),
                "health_projects": sum(
                    v for k, v in health_counts.items() if k in ["H1", "H2"]
                )
            }
        }

    @staticmethod
    def _generate_project_monthly(
        db: Session,
        project_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成项目月报"""
        # 复用周报逻辑，增加趋势数据
        data = TemplateReportService._generate_project_weekly(
            db, project_id, start_date, end_date, sections_config, metrics_config
        )

        # 添加周度趋势
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

        data["sections"]["weekly_trend"] = {
            "title": "周度趋势",
            "type": "line",
            "data": weeks
        }

        return data

    @staticmethod
    def _generate_dept_monthly(
        db: Session,
        department_id: int,
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成部门月报"""
        # 复用周报逻辑
        data = TemplateReportService._generate_dept_weekly(
            db, department_id, start_date, end_date, sections_config, metrics_config
        )

        return data

    @staticmethod
    def _generate_generic_report(
        db: Session,
        report_type: str,
        project_id: Optional[int],
        department_id: Optional[int],
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """生成通用报表"""
        return {
            "report_type": report_type,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "sections": {},
            "metrics": {},
            "message": "该报表类型待扩展"


# 创建单例
template_report_service = TemplateReportService()
