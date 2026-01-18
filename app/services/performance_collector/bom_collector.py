# -*- coding: utf-8 -*-
"""
工程师绩效数据采集 - BOM数据收集
"""

from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem
from app.models.project import ProjectMember
from .base import PerformanceDataCollectorBase


class BomCollector(PerformanceDataCollectorBase):
    """BOM数据收集器"""

    def collect_bom_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集BOM相关数据（增强版：包含异常处理）"""
        try:
            # 获取工程师参与的项目
            project_ids = [
                pm.project_id for pm in self.db.query(ProjectMember.project_id).filter(
                    ProjectMember.user_id == engineer_id
                ).all()
            ]

            if not project_ids:
                return {
                    'total_bom': 0,
                    'on_time_bom': 0,
                    'bom_timeliness_rate': 0.0,
                    'standard_part_rate': 0.0,
                    'reuse_rate': 0.0
                }

            # 统计BOM提交情况
            bom_headers = self.db.query(BomHeader).filter(
                BomHeader.project_id.in_(project_ids),
                BomHeader.created_at.between(start_date, end_date)
            ).all()

            total_bom = len(bom_headers)
            on_time_bom = sum(
                1 for bom in bom_headers
                if bom.due_date and bom.submitted_at
                and bom.submitted_at <= bom.due_date
            )

            bom_timeliness_rate = (on_time_bom / total_bom * 100) if total_bom > 0 else 0.0

            # 统计标准件使用率
            try:
                bom_items = self.db.query(BomItem).join(
                    BomHeader, BomItem.bom_id == BomHeader.id
                ).filter(
                    BomHeader.project_id.in_(project_ids),
                    BomHeader.created_at.between(start_date, end_date)
                ).all()

                if bom_items:
                    standard_items = sum(1 for item in bom_items if getattr(item, 'is_standard', False))
                    standard_part_rate = (standard_items / len(bom_items) * 100)
                else:
                    standard_part_rate = 0.0
            except Exception:
                standard_part_rate = 0.0

            return {
                'total_bom': total_bom,
                'on_time_bom': on_time_bom,
                'bom_timeliness_rate': round(bom_timeliness_rate, 2),
                'standard_part_rate': round(standard_part_rate, 2),
                'reuse_rate': 0.0  # 需要从设计复用记录中统计
            }
        except Exception as e:
            return {
                'total_bom': 0,
                'on_time_bom': 0,
                'bom_timeliness_rate': 0.0,
                'standard_part_rate': 0.0,
                'reuse_rate': 0.0,
                'error': str(e)
            }
