# -*- coding: utf-8 -*-
"""
工程师绩效数据采集 - ECN数据收集
"""

from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.ecn import Ecn
from app.models.project import ProjectMember
from .base import PerformanceDataCollectorBase


class EcnCollector(PerformanceDataCollectorBase):
    """ECN数据收集器"""

    def collect_ecn_responsibility_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集ECN责任数据（增强版：包含异常处理）"""
        try:
            # 获取工程师参与的项目
            project_ids = [
                pm.project_id for pm in self.db.query(ProjectMember.project_id).filter(
                    ProjectMember.user_id == engineer_id
                ).all()
            ]

            if not project_ids:
                return {
                    'total_ecn': 0,
                    'responsible_ecn': 0,
                    'ecn_responsibility_rate': 0.0
                }

            # 统计总ECN数
            total_ecn = self.db.query(Ecn).filter(
                Ecn.project_id.in_(project_ids),
                Ecn.created_at.between(start_date, end_date)
            ).count()

            # 统计因设计问题产生的ECN（通过ECN类型判断）
            responsible_ecn = self.db.query(Ecn).filter(
                Ecn.project_id.in_(project_ids),
                Ecn.created_at.between(start_date, end_date),
                Ecn.ecn_type.in_(['DESIGN_CHANGE', 'MECHANICAL_SCHEME', 'ELECTRICAL_SCHEME'])
            ).count()

            ecn_rate = (responsible_ecn / len(project_ids) * 100) if project_ids else 0.0

            return {
                'total_ecn': total_ecn,
                'responsible_ecn': responsible_ecn,
                'ecn_responsibility_rate': round(ecn_rate, 2)
            }
        except Exception as e:
            return {
                'total_ecn': 0,
                'responsible_ecn': 0,
                'ecn_responsibility_rate': 0.0,
                'error': str(e)
            }
