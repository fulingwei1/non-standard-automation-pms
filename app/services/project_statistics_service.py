# -*- coding: utf-8 -*-
"""
项目统一统计服务

提供项目中心各模块的统一统计功能，减少代码重复
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project


def calculate_status_statistics(query) -> Dict[str, int]:
    """计算状态统计"""
    projects = query.all()
    stats = {}
    for p in projects:
        if p.status:
            stats[p.status] = stats.get(p.status, 0) + 1
    return stats


def calculate_stage_statistics(query) -> Dict[str, int]:
    """计算阶段统计"""
    projects = query.all()
    stats = {}
    for p in projects:
        if p.stage:
            stats[p.stage] = stats.get(p.stage, 0) + 1
    return stats


def calculate_health_statistics(query) -> Dict[str, int]:
    """计算健康度统计"""
    projects = query.all()
    stats = {}
    for p in projects:
        if p.health:
            stats[p.health] = stats.get(p.health, 0) + 1
    return stats


def calculate_pm_statistics(query) -> List[Dict[str, Any]]:
    """计算项目经理统计"""
    projects = query.all()
    temp_stats = {}
    for p in projects:
        if p.pm_id:
            if p.pm_id not in temp_stats:
                temp_stats[p.pm_id] = {
                    "pm_id": p.pm_id,
                    "pm_name": p.pm_name or "未知",
                    "count": 0,
                }
            temp_stats[p.pm_id]["count"] += 1
    return list(temp_stats.values())


def calculate_customer_statistics(query) -> List[Dict[str, Any]]:
    """计算客户统计"""
    projects = query.all()
    temp_stats = {}
    for p in projects:
        cid = p.customer_id or 0
        cname = p.customer_name or "未知客户"
        if cid not in temp_stats:
            temp_stats[cid] = {
                "customer_id": cid,
                "customer_name": cname,
                "count": 0,
                "total_amount": 0.0,
            }
        temp_stats[cid]["count"] += 1
        temp_stats[cid]["total_amount"] += float(p.contract_amount or 0)
    return list(temp_stats.values())


def calculate_monthly_statistics(
    query, start_date=None, end_date=None
) -> List[Dict[str, Any]]:
    """计算月度统计"""
    from datetime import datetime

    if start_date:
        query = query.filter(
            Project.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query = query.filter(
            Project.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    projects = query.all()
    temp_stats = {}
    for p in projects:
        if p.created_at:
            key = (p.created_at.year, p.created_at.month)
            if key not in temp_stats:
                temp_stats[key] = {
                    "year": p.created_at.year,
                    "month": p.created_at.month,
                    "month_label": f"{p.created_at.year}-{p.created_at.month:02d}",
                    "count": 0,
                    "total_amount": 0.0,
                }
            temp_stats[key]["count"] += 1
            temp_stats[key]["total_amount"] += float(p.contract_amount or 0)

    # 排序
    sorted_keys = sorted(temp_stats.keys())
    return [temp_stats[k] for k in sorted_keys]


def build_project_statistics(
    db, query, group_by=None, start_date=None, end_date=None
) -> Dict[str, Any]:
    """构建综合统计数据"""
    projects = query.all()
    total = len(projects)
    avg_progress = (
        sum(p.progress_pct or 0 for p in projects) / total if total > 0 else 0
    )

    result = {
        "total": total,
        "average_progress": avg_progress,
        "by_status": calculate_status_statistics(query),
        "by_stage": calculate_stage_statistics(query),
        "by_health": calculate_health_statistics(query),
        "by_pm": calculate_pm_statistics(query),
    }

    if group_by == "customer":
        result["by_customer"] = calculate_customer_statistics(query)
    elif group_by == "month":
        result["by_month"] = calculate_monthly_statistics(query, start_date, end_date)

    return result


class ProjectStatisticsServiceBase(ABC):
    """项目统计服务基类"""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def get_model(self):
        """返回要统计的模型类"""
        pass

    @abstractmethod
    def get_project_id_field(self) -> str:
        """返回项目ID字段名"""
        pass

    def get_project(self, project_id: int) -> Project:
        """获取项目信息"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        return project

    def build_base_query(self, project_id: int):
        """构建基础查询"""
        model = self.get_model()
        project_id_field = getattr(model, self.get_project_id_field())
        return self.db.query(model).filter(project_id_field == project_id)

    def apply_date_filter(
        self,
        query,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        date_field: str = "created_at",
    ):
        """应用日期范围筛选"""
        model = self.get_model()
        date_attr = getattr(model, date_field, None)

        if date_attr and start_date:
            query = query.filter(date_attr >= start_date)
        if date_attr and end_date:
            query = query.filter(date_attr <= end_date)

        return query

    def group_by_field(
        self,
        query,
        field_name: str,
        aggregate_func=func.sum,
        aggregate_field: Optional[str] = None,
    ) -> Dict[str, Any]:
        """按字段分组统计"""
        model = self.get_model()
        field_attr = getattr(model, field_name, None)

        if not field_attr:
            return {}

        if aggregate_field:
            aggregate_attr = getattr(model, aggregate_field)
            result = (
                query.with_entities(
                    field_attr, aggregate_func(aggregate_attr).label("total")
                )
                .group_by(field_attr)
                .all()
            )
        else:
            result = (
                query.with_entities(field_attr, func.count().label("total"))
                .group_by(field_attr)
                .all()
            )

        return {
            str(key): float(value) if isinstance(value, Decimal) else value
            for key, value in result
        }

    def calculate_total(
        self,
        query,
        field_name: str,
    ) -> float:
        """计算总和"""
        model = self.get_model()
        field_attr = getattr(model, field_name, None)

        if not field_attr:
            return 0.0

        total = query.with_entities(func.sum(field_attr)).scalar()
        return float(total) if total else 0.0

    def calculate_avg(
        self,
        query,
        field_name: str,
    ) -> float:
        """计算平均值"""
        model = self.get_model()
        field_attr = getattr(model, field_name, None)

        if not field_attr:
            return 0.0

        avg = query.with_entities(func.avg(field_attr)).scalar()
        return float(avg) if avg else 0.0

    def count_distinct(
        self,
        query,
        field_name: str,
    ) -> int:
        """计算不重复数量"""
        model = self.get_model()
        field_attr = getattr(model, field_name, None)

        if not field_attr:
            return 0

        count = query.with_entities(func.count(func.distinct(field_attr))).scalar()
        return count or 0

    @abstractmethod
    def get_summary(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """获取汇总数据（子类实现）"""
        pass


class CostStatisticsService(ProjectStatisticsServiceBase):
    """成本统计服务"""

    def get_model(self):
        from app.models.project import ProjectCost

        return ProjectCost

    def get_project_id_field(self) -> str:
        return "project_id"

    def get_summary(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """获取成本汇总"""
        project = self.get_project(project_id)
        query = self.build_base_query(project_id)
        query = self.apply_date_filter(query, start_date, end_date, "created_at")

        # 按类型汇总
        by_type = self.group_by_field(query, "cost_type", func.sum, "amount")

        # 总成本
        total_cost = self.calculate_total(query, "amount")

        # 预算使用率
        budget_used_pct = None
        if project.budget_amount and project.budget_amount > 0:
            budget_used_pct = round(total_cost / float(project.budget_amount) * 100, 2)

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "total_cost": total_cost,
            "by_type": by_type,
            "budget": float(project.budget_amount) if project.budget_amount else None,
            "budget_used_pct": budget_used_pct,
        }


class TimesheetStatisticsService(ProjectStatisticsServiceBase):
    """工时统计服务"""

    def get_model(self):
        from app.models.timesheet import Timesheet

        return Timesheet

    def get_project_id_field(self) -> str:
        return "project_id"

    def get_summary(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """获取工时汇总"""
        project = self.get_project(project_id)
        query = self.build_base_query(project_id)
        query = query.filter(self.get_model().status == "APPROVED")
        query = self.apply_date_filter(query, start_date, end_date, "work_date")

        timesheets = query.all()

        # 统计汇总
        total_hours = Decimal("0")
        by_user: Dict[str, Dict[str, Any]] = {}
        by_date: Dict[str, Decimal] = {}
        by_work_type: Dict[str, Decimal] = {}
        participants = set()

        for ts in timesheets:
            hours = Decimal(str(ts.hours or 0))
            total_hours += hours
            participants.add(ts.user_id)

            # 按用户统计
            from app.models.user import User

            user = self.db.query(User).filter(User.id == ts.user_id).first()
            user_name = user.real_name or user.username if user else f"用户{ts.user_id}"
            if user_name not in by_user:
                by_user[user_name] = {
                    "user_id": ts.user_id,
                    "user_name": user_name,
                    "total_hours": Decimal("0"),
                    "days": 0,
                }
            by_user[user_name]["total_hours"] += hours
            by_user[user_name]["days"] += 1

            # 按日期统计
            date_str = ts.work_date.isoformat()
            if date_str not in by_date:
                by_date[date_str] = Decimal("0")
            by_date[date_str] += hours

            # 按工作类型统计
            work_type = ts.overtime_type or "NORMAL"
            if work_type not in by_work_type:
                by_work_type[work_type] = Decimal("0")
            by_work_type[work_type] += hours

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "total_hours": float(total_hours),
            "total_participants": len(participants),
            "by_user": [
                {**v, "total_hours": float(v["total_hours"])} for v in by_user.values()
            ],
            "by_date": {k: float(v) for k, v in by_date.items()},
            "by_work_type": {k: float(v) for k, v in by_work_type.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }

    def get_statistics(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """获取工时统计"""
        project = self.get_project(project_id)
        query = self.build_base_query(project_id)
        query = self.apply_date_filter(query, start_date, end_date, "work_date")

        all_timesheets = query.all()

        # 统计各状态的工时
        total_hours = Decimal("0")
        draft_hours = Decimal("0")
        pending_hours = Decimal("0")
        approved_hours = Decimal("0")
        rejected_hours = Decimal("0")

        for ts in all_timesheets:
            hours = Decimal(str(ts.hours or 0))
            total_hours += hours
            if ts.status == "DRAFT":
                draft_hours += hours
            elif ts.status == "PENDING":
                pending_hours += hours
            elif ts.status == "APPROVED":
                approved_hours += hours
            elif ts.status == "REJECTED":
                rejected_hours += hours

        # 计算平均每日工时
        unique_dates = set(ts.work_date for ts in all_timesheets if ts.work_date)
        avg_daily_hours = (
            float(total_hours) / len(unique_dates) if unique_dates else 0.0
        )

        # 计算参与人数
        participants = set(ts.user_id for ts in all_timesheets)

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "total_hours": float(total_hours),
            "approved_hours": float(approved_hours),
            "pending_hours": float(pending_hours),
            "draft_hours": float(draft_hours),
            "rejected_hours": float(rejected_hours),
            "total_records": len(all_timesheets),
            "total_participants": len(participants),
            "unique_work_days": len(unique_dates),
            "avg_daily_hours": round(avg_daily_hours, 2),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }


class WorkLogStatisticsService(ProjectStatisticsServiceBase):
    """工作日志统计服务"""

    def get_model(self):
        from app.models.work_log import WorkLog

        return WorkLog

    def get_project_id_field(self) -> str:
        # 工作日志通过WorkLogMention关联，不直接有project_id字段
        return "id"

    def get_summary(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """获取工作日志汇总"""
        from datetime import timedelta
        from app.models.work_log import WorkLog, WorkLogMention

        project = self.get_project(project_id)

        # 如果没有指定日期范围，使用最近N天
        if not start_date:
            start_date = date.today() - timedelta(days=days)

        # 查询提及该项目的工作日志
        query = (
            self.db.query(WorkLog)
            .join(WorkLogMention, WorkLog.id == WorkLogMention.work_log_id)
            .filter(
                WorkLogMention.mention_type == "PROJECT",
                WorkLogMention.mention_id == project_id,
                WorkLog.work_date >= start_date,
            )
        )

        if end_date:
            query = query.filter(WorkLog.work_date <= end_date)

        # 统计
        stats = query.with_entities(
            func.count(func.distinct(WorkLog.id)).label("log_count"),
            func.count(func.distinct(WorkLog.user_id)).label("contributor_count"),
        ).first()

        return {
            "project_id": project_id,
            "period_days": days,
            "log_count": stats.log_count if stats else 0,
            "contributor_count": stats.contributor_count if stats else 0,
        }
