# -*- coding: utf-8 -*-
"""
排名统计服务
负责绩效排名、统计和趋势分析
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.performance import PerformancePeriod, PerformanceResult


class RankingService:
    """排名统计服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_ranking(
        self,
        period_id: int,
        job_type: Optional[str] = None,
        job_level: Optional[str] = None,
        department_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[PerformanceResult], int]:
        """获取绩效排名"""
        query = self.db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period_id,
            PerformanceResult.job_type.isnot(None)
        )

        if job_type:
            query = query.filter(PerformanceResult.job_type == job_type)
        if job_level:
            query = query.filter(PerformanceResult.job_level == job_level)
        if department_id:
            query = query.filter(PerformanceResult.department_id == department_id)

        total = query.count()
        items = query.order_by(
            desc(PerformanceResult.total_score)
        ).offset(offset).limit(limit).all()

        return items, total

    def get_company_summary(self, period_id: int) -> Dict[str, Any]:
        """获取公司整体概况"""
        results = self.db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period_id,
            PerformanceResult.job_type.isnot(None)
        ).all()

        if not results:
            return {}

        # 按岗位类型统计
        by_job_type = self._analyze_by_job_type(results)

        # 等级分布
        level_distribution = self._analyze_level_distribution(results)

        # 总体统计
        all_scores = [float(r.total_score or 0) for r in results]

        return {
            'total_engineers': len(results),
            'by_job_type': by_job_type,
            'level_distribution': level_distribution,
            'avg_score': round(sum(all_scores) / len(all_scores), 2),
            'max_score': max(all_scores),
            'min_score': min(all_scores)
        }

    def _analyze_by_job_type(self, results: List[PerformanceResult]) -> Dict[str, Dict]:
        """按岗位类型分析"""
        by_job_type = {}
        for job_type in ['mechanical', 'test', 'electrical']:
            type_results = [r for r in results if r.job_type == job_type]
            if type_results:
                scores = [float(r.total_score or 0) for r in type_results]
                by_job_type[job_type] = {
                    'count': len(type_results),
                    'avg_score': round(sum(scores) / len(scores), 2),
                    'max_score': max(scores),
                    'min_score': min(scores)
                }
        return by_job_type

    def _analyze_level_distribution(self, results: List[PerformanceResult]) -> Dict[str, int]:
        """分析等级分布"""
        level_distribution = {}
        for result in results:
            level = result.level or 'D'
            level_distribution[level] = level_distribution.get(level, 0) + 1
        return level_distribution

    def get_engineer_trend(
        self, engineer_id: int, periods: int = 6
    ) -> List[Dict[str, Any]]:
        """获取工程师历史趋势"""
        results = self.db.query(PerformanceResult).join(
            PerformancePeriod, PerformanceResult.period_id == PerformancePeriod.id
        ).filter(
            PerformanceResult.user_id == engineer_id
        ).order_by(
            desc(PerformancePeriod.start_date)
        ).limit(periods).all()

        trends = []
        for r in reversed(results):
            trends.append({
                'period_id': r.period_id,
                'period_name': r.period.period_name if r.period else '',
                'total_score': float(r.total_score or 0),
                'level': r.level,
                'rank': r.company_rank
            })
        return trends
