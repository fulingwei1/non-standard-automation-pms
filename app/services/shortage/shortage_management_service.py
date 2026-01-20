# -*- coding: utf-8 -*-
"""
缺料管理服务
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.project import Project
from app.models.shortage import ShortageReport
from app.models.user import User
from app.schemas.common import PaginatedResponse


class ShortageManagementService:
    """缺料管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_shortage_list(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        urgent_level: Optional[str] = None,
    ) -> PaginatedResponse:
        """
        获取缺料列表

        Args:
            page: 页码
            page_size: 每页数量
            keyword: 关键词搜索（物料编码或名称）
            status: 状态筛选
            project_id: 项目ID筛选
            urgent_level: 紧急程度筛选

        Returns:
            PaginatedResponse: 分页响应
        """
        query = self.db.query(ShortageReport)

        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    ShortageReport.material_code.ilike(f"%{keyword}%"),
                    ShortageReport.material_name.ilike(f"%{keyword}%"),
                    ShortageReport.report_no.ilike(f"%{keyword}%"),
                )
            )

        # 状态筛选
        if status:
            query = query.filter(ShortageReport.status == status)

        # 项目筛选
        if project_id:
            query = query.filter(ShortageReport.project_id == project_id)

        # 紧急程度筛选
        if urgent_level:
            query = query.filter(ShortageReport.urgent_level == urgent_level)

        # 计算总数
        total = query.count()

        # 排序并分页
        query = query.order_by(desc(ShortageReport.created_at))
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        # 构建响应项
        items = []
        for record in records:
            # 获取关联的项目名称
            project_name = None
            if record.project_id:
                project = self.db.query(Project).filter(Project.id == record.project_id).first()
                if project:
                    project_name = project.project_name

            # 获取上报人名称
            reporter_name = None
            if record.reporter_id:
                reporter = self.db.query(User).filter(User.id == record.reporter_id).first()
                if reporter:
                    reporter_name = reporter.real_name or reporter.username

            items.append({
                "id": record.id,
                "report_no": record.report_no,
                "project_id": record.project_id,
                "project_name": project_name,
                "material_id": record.material_id,
                "material_code": record.material_code,
                "material_name": record.material_name,
                "required_qty": float(record.required_qty) if record.required_qty else 0,
                "shortage_qty": float(record.shortage_qty) if record.shortage_qty else 0,
                "urgent_level": record.urgent_level,
                "status": record.status,
                "reporter_id": record.reporter_id,
                "reporter_name": reporter_name,
                "report_time": record.report_time.isoformat() if record.report_time else None,
                "solution_type": record.solution_type,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            })

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    def create_shortage_record(self, data: Dict[str, Any], current_user: User) -> Dict[str, Any]:
        """
        创建缺料记录

        Args:
            data: 缺料记录数据
            current_user: 当前用户

        Returns:
            dict: 创建结果
        """
        # 生成上报单号
        today = date.today()
        count = self.db.query(ShortageReport).filter(
            func.date(ShortageReport.created_at) == today
        ).count()
        report_no = f"SR{today.strftime('%Y%m%d')}{count + 1:03d}"

        # 获取物料信息
        material = self.db.query(Material).filter(Material.id == data.get("material_id")).first()
        if not material:
            return {"success": False, "message": "物料不存在"}

        # 创建缺料记录
        record = ShortageReport(
            report_no=report_no,
            project_id=data.get("project_id"),
            machine_id=data.get("machine_id"),
            work_order_id=data.get("work_order_id"),
            reporter_id=current_user.id,
            report_time=datetime.now(),
            report_location=data.get("report_location"),
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            required_qty=Decimal(str(data.get("required_qty", 0))),
            shortage_qty=Decimal(str(data.get("shortage_qty", 0))),
            urgent_level=data.get("urgent_level", "NORMAL"),
            status="REPORTED",
            remark=data.get("remark"),
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return {
            "success": True,
            "message": "缺料记录创建成功",
            "data": {
                "id": record.id,
                "report_no": record.report_no,
            }
        }

    def get_shortage_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取缺料统计

        Args:
            project_id: 可选的项目ID筛选

        Returns:
            dict: 统计数据
        """
        query = self.db.query(ShortageReport)

        if project_id:
            query = query.filter(ShortageReport.project_id == project_id)

        # 总数统计
        total_count = query.count()

        # 按状态统计
        status_stats = {}
        status_query = self.db.query(
            ShortageReport.status,
            func.count(ShortageReport.id).label("count")
        )
        if project_id:
            status_query = status_query.filter(ShortageReport.project_id == project_id)
        status_results = status_query.group_by(ShortageReport.status).all()

        for status, count in status_results:
            status_stats[status or "UNKNOWN"] = count

        # 按紧急程度统计
        urgent_stats = {}
        urgent_query = self.db.query(
            ShortageReport.urgent_level,
            func.count(ShortageReport.id).label("count")
        )
        if project_id:
            urgent_query = urgent_query.filter(ShortageReport.project_id == project_id)
        urgent_results = urgent_query.group_by(ShortageReport.urgent_level).all()

        for level, count in urgent_results:
            urgent_stats[level or "NORMAL"] = count

        # 最近7天趋势
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_stats = []
        daily_query = self.db.query(
            func.date(ShortageReport.created_at).label("date"),
            func.count(ShortageReport.id).label("count")
        ).filter(
            ShortageReport.created_at >= seven_days_ago
        )
        if project_id:
            daily_query = daily_query.filter(ShortageReport.project_id == project_id)
        daily_results = daily_query.group_by(
            func.date(ShortageReport.created_at)
        ).order_by(func.date(ShortageReport.created_at)).all()

        for d, count in daily_results:
            daily_stats.append({
                "date": d.isoformat() if d else None,
                "count": count
            })

        # 待处理数量
        pending_count = query.filter(
            ShortageReport.status.in_(["REPORTED", "CONFIRMED", "HANDLING"])
        ).count()

        # 已解决数量
        resolved_count = query.filter(ShortageReport.status == "RESOLVED").count()

        return {
            "total_count": total_count,
            "pending_count": pending_count,
            "resolved_count": resolved_count,
            "by_status": status_stats,
            "by_urgent_level": urgent_stats,
            "daily_trend": daily_stats,
        }
