# -*- coding: utf-8 -*-
"""
齐套率统计服务
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.material import BomItem
from app.models.project import Project
from app.services.kit_rate import KitRateService
from app.common.date_range import get_month_range


def calculate_date_range(today: date) -> Tuple[date, date]:
    """
    计算默认日期范围（当前月）

    Returns:
        Tuple[date, date]: (开始日期, 结束日期)
    """
    start_date, end_date = get_month_range(today)

    return start_date, end_date


def get_project_bom_items(
    db: Session,
    project_id: int
) -> List[BomItem]:
    """
    获取项目的所有BOM物料项

    Returns:
        List[BomItem]: BOM物料项列表
    """
    service = KitRateService(db)
    return service.list_bom_items_for_project(project_id)


def calculate_project_kit_statistics(
    db: Session,
    project: Project
) -> Optional[Dict[str, Any]]:
    """
    计算单个项目的齐套率统计

    Returns:
        Optional[Dict[str, Any]]: 统计结果字典，如果计算失败返回None
    """
    try:
        service = KitRateService(db)
        all_bom_items = get_project_bom_items(db, project.id)
        kit_data = service.calculate_kit_rate(all_bom_items, "quantity")

        return {
            "project_id": project.id,
            "project_name": project.project_name,
            "project_code": project.project_code,
            "kit_rate": kit_data.get("kit_rate", 0.0),
            "total_items": kit_data.get("total_items", 0),
            "fulfilled_items": kit_data.get("fulfilled_items", 0),
            "shortage_items": kit_data.get("shortage_items", 0),
            "in_transit_items": kit_data.get("in_transit_items", 0),
            "kit_status": kit_data.get("kit_status", "shortage"),
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"计算项目 {project.id} 齐套率失败: {str(e)}")
        return None


def calculate_workshop_kit_statistics(
    db: Session,
    workshop_id: Optional[int],
    projects: List[Project]
) -> List[Dict[str, Any]]:
    """
    按车间统计齐套率

    Returns:
        List[Dict[str, Any]]: 车间统计列表
    """
    from app.models.production import Workshop
    service = KitRateService(db)

    workshops = db.query(Workshop).all()
    if workshop_id:
        workshops = [w for w in workshops if w.id == workshop_id]

    statistics = []

    for workshop in workshops:
        # 获取该车间的所有项目（简化处理，实际应该关联车间）
        workshop_projects = [p for p in projects if p.id]

        total_kit_rate = 0.0
        project_count = 0
        total_items = 0
        fulfilled_items = 0
        shortage_items = 0
        in_transit_items = 0

        for project in workshop_projects:
            try:
                all_bom_items = get_project_bom_items(db, project.id)
                kit_data = service.calculate_kit_rate(all_bom_items, "quantity")

                total_kit_rate += kit_data.get("kit_rate", 0.0)
                project_count += 1
                total_items += kit_data.get("total_items", 0)
                fulfilled_items += kit_data.get("fulfilled_items", 0)
                shortage_items += kit_data.get("shortage_items", 0)
                in_transit_items += kit_data.get("in_transit_items", 0)
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                continue

        avg_kit_rate = total_kit_rate / project_count if project_count > 0 else 0.0

        statistics.append({
            "workshop_id": workshop.id,
            "workshop_name": workshop.workshop_name,
            "kit_rate": round(avg_kit_rate, 2),
            "project_count": project_count,
            "total_items": total_items,
            "fulfilled_items": fulfilled_items,
            "shortage_items": shortage_items,
            "in_transit_items": in_transit_items,
        })

    return statistics


def calculate_daily_kit_statistics(
    db: Session,
    start_date: date,
    end_date: date,
    projects: List[Project]
) -> List[Dict[str, Any]]:
    """
    按日期统计齐套率

    Returns:
        List[Dict[str, Any]]: 日期统计列表
    """
    statistics = []
    current = start_date
    service = KitRateService(db)

    while current <= end_date:
        # 简化处理：使用当前数据，实际应该从历史记录表查询
        total_kit_rate = 0.0
        project_count = 0

        for project in projects:
            try:
                all_bom_items = get_project_bom_items(db, project.id)
                kit_data = service.calculate_kit_rate(all_bom_items, "quantity")

                total_kit_rate += kit_data.get("kit_rate", 0.0)
                project_count += 1
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                continue

        avg_kit_rate = total_kit_rate / project_count if project_count > 0 else 0.0

        statistics.append({
            "date": current.isoformat(),
            "kit_rate": round(avg_kit_rate, 2),
            "project_count": project_count,
        })

        current += timedelta(days=1)

    return statistics


def calculate_summary_statistics(
    statistics: List[Dict[str, Any]],
    group_by: str
) -> Dict[str, Any]:
    """
    计算汇总统计

    Returns:
        Dict[str, Any]: 汇总统计字典
    """
    if not statistics:
        return {
            "avg_kit_rate": 0.0,
            "max_kit_rate": 0.0,
            "min_kit_rate": 0.0,
            "total_count": 0,
        }

    if group_by in ["project", "workshop"]:
        avg_kit_rate = sum(s["kit_rate"] for s in statistics) / len(statistics)
        max_kit_rate = max(s["kit_rate"] for s in statistics)
        min_kit_rate = min(s["kit_rate"] for s in statistics)
    else:  # day
        avg_kit_rate = sum(s["kit_rate"] for s in statistics) / len(statistics)
        max_kit_rate = max(s["kit_rate"] for s in statistics)
        min_kit_rate = min(s["kit_rate"] for s in statistics)

    return {
        "avg_kit_rate": round(avg_kit_rate, 2),
        "max_kit_rate": round(max_kit_rate, 2),
        "min_kit_rate": round(min_kit_rate, 2),
        "total_count": len(statistics),
    }
