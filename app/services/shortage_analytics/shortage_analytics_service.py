# -*- coding: utf-8 -*-
"""
ShortageAnalyticsService - 缺料分析业务服务
提取自 app/api/v1/endpoints/shortage/analytics/dashboard.py
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.material import MaterialShortage
from app.models.project import Project
from app.models.shortage import (
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageDailyReport,
    ShortageReport,
)


class ShortageAnalyticsService:
    """缺料分析服务"""

    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db

    def get_dashboard_data(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取缺料看板数据
        
        Args:
            project_id: 项目ID筛选（可选）
            
        Returns:
            包含缺料上报、预警、到货、替代、调拨统计的字典
        """
        # === 缺料上报统计 (ShortageReport) ===
        report_query = self.db.query(ShortageReport)
        if project_id:
            report_query = report_query.filter(ShortageReport.project_id == project_id)

        total_reports = report_query.count()
        reported = report_query.filter(ShortageReport.status == 'REPORTED').count()
        confirmed = report_query.filter(ShortageReport.status == 'CONFIRMED').count()
        handling = report_query.filter(ShortageReport.status == 'HANDLING').count()
        resolved = report_query.filter(ShortageReport.status == 'RESOLVED').count()

        # 紧急缺料
        urgent_reports = report_query.filter(
            ShortageReport.urgent_level.in_(['URGENT', 'CRITICAL']),
            ShortageReport.status != 'RESOLVED'
        ).count()

        # === 系统检测的缺料预警 (MaterialShortage) ===
        alert_query = self.db.query(MaterialShortage)
        if project_id:
            alert_query = alert_query.filter(MaterialShortage.project_id == project_id)

        total_alerts = alert_query.count()
        unresolved_alerts = alert_query.filter(MaterialShortage.status != "RESOLVED").count()
        critical_alerts = alert_query.filter(
            MaterialShortage.alert_level == "CRITICAL",
            MaterialShortage.status != "RESOLVED"
        ).count()

        # === 到货跟踪统计 ===
        arrival_query = self.db.query(MaterialArrival)
        total_arrivals = arrival_query.count()
        pending_arrivals = arrival_query.filter(MaterialArrival.status == 'PENDING').count()
        delayed_arrivals = arrival_query.filter(MaterialArrival.is_delayed).count()

        # === 物料替代统计 ===
        sub_query = self.db.query(MaterialSubstitution)
        if project_id:
            sub_query = sub_query.filter(MaterialSubstitution.project_id == project_id)
        total_substitutions = sub_query.count()
        pending_substitutions = sub_query.filter(
            MaterialSubstitution.status.in_(['DRAFT', 'TECH_PENDING', 'PROD_PENDING'])
        ).count()

        # === 物料调拨统计 ===
        transfer_query = self.db.query(MaterialTransfer)
        if project_id:
            transfer_query = transfer_query.filter(
                (MaterialTransfer.from_project_id == project_id) |
                (MaterialTransfer.to_project_id == project_id)
            )
        total_transfers = transfer_query.count()
        pending_transfers = transfer_query.filter(
            MaterialTransfer.status.in_(['DRAFT', 'PENDING'])
        ).count()

        # === 最近缺料上报 ===
        recent_reports = self._get_recent_reports(project_id)

        return {
            "reports": {
                "total": total_reports,
                "reported": reported,
                "confirmed": confirmed,
                "handling": handling,
                "resolved": resolved,
                "urgent": urgent_reports
            },
            "alerts": {
                "total": total_alerts,
                "unresolved": unresolved_alerts,
                "critical": critical_alerts
            },
            "arrivals": {
                "total": total_arrivals,
                "pending": pending_arrivals,
                "delayed": delayed_arrivals
            },
            "substitutions": {
                "total": total_substitutions,
                "pending": pending_substitutions
            },
            "transfers": {
                "total": total_transfers,
                "pending": pending_transfers
            },
            "recent_reports": recent_reports
        }

    def _get_recent_reports(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取最近的缺料上报列表
        
        Args:
            project_id: 项目ID筛选（可选）
            
        Returns:
            最近10条缺料上报的列表
        """
        recent_query = self.db.query(ShortageReport)
        if project_id:
            recent_query = recent_query.filter(ShortageReport.project_id == project_id)
        recent_reports = recent_query.order_by(desc(ShortageReport.created_at)).limit(10).all()

        recent_reports_list = []
        for report in recent_reports:
            project = self.db.query(Project).filter(Project.id == report.project_id).first()
            recent_reports_list.append({
                "id": report.id,
                "report_no": report.report_no,
                "project_id": report.project_id,
                "project_name": project.project_name if project else None,
                "material_name": report.material_name,
                "shortage_qty": float(report.shortage_qty),
                "urgent_level": report.urgent_level,
                "status": report.status,
                "report_time": str(report.report_time) if report.report_time else None,
            })

        return recent_reports_list

    def get_daily_report(
        self, 
        report_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取缺料日报（实时计算）
        
        Args:
            report_date: 报表日期（默认今天）
            project_id: 项目ID筛选（可选）
            
        Returns:
            包含当日缺料统计的字典
        """
        if not report_date:
            report_date = date.today()

        # 查询当日缺料上报
        query = self.db.query(ShortageReport).filter(
            func.date(ShortageReport.report_time) == report_date
        )
        if project_id:
            query = query.filter(ShortageReport.project_id == project_id)

        daily_reports = query.all()

        # 按紧急程度统计
        by_urgent: Dict[str, int] = {}
        for report in daily_reports:
            level = report.urgent_level
            by_urgent[level] = by_urgent.get(level, 0) + 1

        # 按状态统计
        by_status: Dict[str, int] = {}
        for report in daily_reports:
            status = report.status
            by_status[status] = by_status.get(status, 0) + 1

        # 按物料统计
        by_material: Dict[str, Dict[str, Any]] = {}
        for report in daily_reports:
            material_key = f"{report.material_id}_{report.material_name}"
            if material_key not in by_material:
                by_material[material_key] = {
                    "material_id": report.material_id,
                    "material_name": report.material_name,
                    "count": 0,
                    "total_shortage_qty": 0.0
                }
            by_material[material_key]["count"] += 1
            by_material[material_key]["total_shortage_qty"] += float(report.shortage_qty)

        # 按项目统计
        by_project: Dict[int, Dict[str, Any]] = {}
        for report in daily_reports:
            if report.project_id not in by_project:
                project = self.db.query(Project).filter(Project.id == report.project_id).first()
                by_project[report.project_id] = {
                    "project_id": report.project_id,
                    "project_name": project.project_name if project else None,
                    "shortage_count": 0,
                    "total_shortage_qty": Decimal("0"),
                    "critical_count": 0
                }
            stats = by_project[report.project_id]
            stats["shortage_count"] += 1
            stats["total_shortage_qty"] += report.shortage_qty
            if report.urgent_level in ['URGENT', 'CRITICAL']:
                stats["critical_count"] += 1

        # 转换 Decimal 为 float
        project_list = []
        for stats in by_project.values():
            project_list.append({
                **stats,
                "total_shortage_qty": float(stats["total_shortage_qty"])
            })

        return {
            "report_date": str(report_date),
            "total_reports": len(daily_reports),
            "by_urgent": by_urgent,
            "by_status": by_status,
            "by_material": list(by_material.values()),
            "by_project": project_list
        }

    def get_latest_daily_report(self) -> Optional[Dict[str, Any]]:
        """
        获取最新缺料日报（预生成数据）
        
        Returns:
            最新日报数据，如果没有数据则返回 None
        """
        latest_date = self.db.query(func.max(ShortageDailyReport.report_date)).scalar()
        if not latest_date:
            return None

        report = self.db.query(ShortageDailyReport).filter(
            ShortageDailyReport.report_date == latest_date
        ).first()

        if not report:
            return None

        return self._build_shortage_daily_report(report)

    def get_daily_report_by_date(self, report_date: date) -> Optional[Dict[str, Any]]:
        """
        按日期获取缺料日报（预生成数据）
        
        Args:
            report_date: 报表日期
            
        Returns:
            指定日期的日报数据，如果没有则返回 None
        """
        report = self.db.query(ShortageDailyReport).filter(
            ShortageDailyReport.report_date == report_date
        ).first()

        if not report:
            return None

        return self._build_shortage_daily_report(report)

    def get_shortage_trends(
        self,
        days: int = 30,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取缺料趋势分析
        
        Args:
            days: 统计天数（7-90天）
            project_id: 项目ID筛选（可选）
            
        Returns:
            包含趋势数据和汇总统计的字典
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # 按天统计缺料上报
        daily_stats = []
        current_date = start_date

        while current_date <= end_date:
            query = self.db.query(ShortageReport).filter(
                func.date(ShortageReport.report_time) == current_date
            )
            if project_id:
                query = query.filter(ShortageReport.project_id == project_id)

            new_count = query.count()
            
            resolved_count = self.db.query(ShortageReport).filter(
                func.date(ShortageReport.resolved_at) == current_date
            )
            if project_id:
                resolved_count = resolved_count.filter(ShortageReport.project_id == project_id)
            resolved_count = resolved_count.count()

            daily_stats.append({
                "date": str(current_date),
                "new": new_count,
                "resolved": resolved_count,
                "net": new_count - resolved_count
            })

            current_date += timedelta(days=1)

        # 计算汇总
        total_new = sum(d["new"] for d in daily_stats)
        total_resolved = sum(d["resolved"] for d in daily_stats)
        avg_daily_new = round(total_new / days, 2) if days > 0 else 0
        avg_daily_resolved = round(total_resolved / days, 2) if days > 0 else 0

        return {
            "period": {"start": str(start_date), "end": str(end_date), "days": days},
            "summary": {
                "total_new": total_new,
                "total_resolved": total_resolved,
                "avg_daily_new": avg_daily_new,
                "avg_daily_resolved": avg_daily_resolved
            },
            "daily": daily_stats
        }

    @staticmethod
    def _build_shortage_daily_report(report: ShortageDailyReport) -> Dict[str, Any]:
        """
        序列化缺料日报（预生成的数据）
        
        Args:
            report: ShortageDailyReport 模型实例
            
        Returns:
            序列化后的字典
        """
        return {
            "date": report.report_date.isoformat(),
            "alerts": {
                "new": report.new_alerts,
                "resolved": report.resolved_alerts,
                "pending": report.pending_alerts,
                "overdue": report.overdue_alerts,
                "levels": {
                    "level1": report.level1_count,
                    "level2": report.level2_count,
                    "level3": report.level3_count,
                    "level4": report.level4_count,
                }
            },
            "reports": {
                "new": report.new_reports,
                "resolved": report.resolved_reports,
            },
            "kit": {
                "total_work_orders": report.total_work_orders,
                "complete_count": report.kit_complete_count,
                "kit_rate": float(report.kit_rate) if report.kit_rate else 0.0,
            },
            "arrivals": {
                "expected": report.expected_arrivals,
                "actual": report.actual_arrivals,
                "delayed": report.delayed_arrivals,
                "on_time_rate": float(report.on_time_rate) if report.on_time_rate else 0.0,
            },
            "response": {
                "avg_response_minutes": report.avg_response_minutes,
                "avg_resolve_hours": float(report.avg_resolve_hours) if report.avg_resolve_hours else 0.0,
            },
            "stoppage": {
                "count": report.stoppage_count,
                "hours": float(report.stoppage_hours) if report.stoppage_hours else 0.0,
            },
        }
