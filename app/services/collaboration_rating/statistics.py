# -*- coding: utf-8 -*-
"""
跨部门协作评价服务 - 统计分析
"""
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import desc

from app.models.engineer_performance import CollaborationRating
from app.models.performance import PerformancePeriod


class RatingStatistics:
    """评价统计分析"""

    def __init__(self, db, service):
        self.db = db
        self.service = service

    def get_average_collaboration_score(
        self,
        engineer_id: int,
        period_id: int
    ) -> Decimal:
        """
        获取平均协作得分

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID

        Returns:
            平均得分（如果无评价则返回默认值75）
        """
        ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.ratee_id == engineer_id,
            CollaborationRating.period_id == period_id,
            CollaborationRating.total_score.isnot(None)
        ).all()

        if not ratings:
            return Decimal('75.0')  # 默认值

        total = sum(r.total_score for r in ratings)
        avg = total / len(ratings)

        return Decimal(str(round(avg, 2)))

    def get_rating_statistics(
        self,
        period_id: int
    ) -> Dict[str, Any]:
        """
        获取评价统计信息

        Args:
            period_id: 考核周期ID

        Returns:
            评价统计信息
        """
        # 获取所有评价记录
        all_ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.period_id == period_id
        ).all()

        total_ratings = len(all_ratings)
        completed_ratings = sum(1 for r in all_ratings if r.total_score is not None)
        pending_ratings = total_ratings - completed_ratings

        completion_rate = (completed_ratings / total_ratings * 100) if total_ratings > 0 else 0.0

        # 计算平均得分
        completed = [r for r in all_ratings if r.total_score is not None]
        avg_score = sum(float(r.total_score) for r in completed) / len(completed) if completed else 0.0

        # 按岗位类型统计
        job_type_stats = {}
        for rating in completed:
            ratee_job_type = rating.ratee_job_type or 'unknown'
            if ratee_job_type not in job_type_stats:
                job_type_stats[ratee_job_type] = {
                    'count': 0,
                    'total_score': 0.0,
                    'avg_score': 0.0
                }
            job_type_stats[ratee_job_type]['count'] += 1
            job_type_stats[ratee_job_type]['total_score'] += float(rating.total_score)

        for job_type in job_type_stats:
            stats = job_type_stats[job_type]
            stats['avg_score'] = round(stats['total_score'] / stats['count'], 2) if stats['count'] > 0 else 0.0

        return {
            'period_id': period_id,
            'total_ratings': total_ratings,
            'completed_ratings': completed_ratings,
            'pending_ratings': pending_ratings,
            'completion_rate': round(completion_rate, 2),
            'average_score': round(avg_score, 2),
            'job_type_statistics': job_type_stats
        }

    def get_collaboration_trend(
        self,
        engineer_id: int,
        periods: int = 6
    ) -> Dict[str, Any]:
        """
        获取跨部门协作趋势

        Args:
            engineer_id: 工程师ID
            periods: 历史周期数

        Returns:
            协作趋势数据
        """
        # 获取最近的几个周期
        recent_periods = self.db.query(PerformancePeriod).order_by(
            desc(PerformancePeriod.start_date)
        ).limit(periods).all()

        trend_data = []
        for period in reversed(recent_periods):  # 从最早到最新
            avg_score = self.get_average_collaboration_score(engineer_id, period.id)
            ratings = self.db.query(CollaborationRating).filter(
                CollaborationRating.ratee_id == engineer_id,
                CollaborationRating.period_id == period.id,
                CollaborationRating.total_score.isnot(None)
            ).count()

            trend_data.append({
                'period_id': period.id,
                'period_name': period.period_name,
                'start_date': period.start_date.isoformat(),
                'end_date': period.end_date.isoformat(),
                'average_score': float(avg_score),
                'rating_count': ratings
            })

        return {
            'engineer_id': engineer_id,
            'trend_data': trend_data,
            'periods_count': len(trend_data)
        }

    def analyze_rating_quality(
        self,
        period_id: int
    ) -> Dict[str, Any]:
        """
        分析评价质量

        Args:
            period_id: 考核周期ID

        Returns:
            评价质量分析
        """
        ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.period_id == period_id,
            CollaborationRating.total_score.isnot(None)
        ).all()

        if not ratings:
            return {
                'total_ratings': 0,
                'quality_analysis': {},
                'recommendations': []
            }

        # 分析评分分布
        scores = [float(r.total_score) for r in ratings]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0

        # 计算标准差
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 0.0
        std_dev = variance ** 0.5

        # 分析各维度得分
        dimension_scores = {
            'communication': [r.communication_score for r in ratings if r.communication_score],
            'response': [r.response_score for r in ratings if r.response_score],
            'delivery': [r.delivery_score for r in ratings if r.delivery_score],
            'interface': [r.interface_score for r in ratings if r.interface_score]
        }

        dimension_analysis = {}
        for dim, scores_list in dimension_scores.items():
            if scores_list:
                dimension_analysis[dim] = {
                    'average': round(sum(scores_list) / len(scores_list), 2),
                    'min': min(scores_list),
                    'max': max(scores_list)
                }

        # 生成建议
        recommendations = []
        if std_dev > 15:  # 标准差过大，评价差异大
            recommendations.append('评价得分差异较大，建议统一评价标准')
        if avg_score < 70:
            recommendations.append('平均得分较低，建议加强跨部门协作培训')
        if len([s for s in scores if s < 60]) > len(scores) * 0.2:  # 超过20%得分低于60
            recommendations.append('存在较多低分评价，建议分析具体原因并改进')

        return {
            'total_ratings': len(ratings),
            'quality_analysis': {
                'average_score': round(avg_score, 2),
                'min_score': round(min_score, 2),
                'max_score': round(max_score, 2),
                'std_deviation': round(std_dev, 2),
                'dimension_analysis': dimension_analysis
            },
            'recommendations': recommendations
        }
