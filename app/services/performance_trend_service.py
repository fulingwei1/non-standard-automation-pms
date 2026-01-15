# -*- coding: utf-8 -*-
"""
绩效趋势分析服务
展示工程师历史6个周期的得分趋势，识别能力变化
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.performance import PerformancePeriod, PerformanceResult
from app.models.engineer_performance import EngineerProfile


class PerformanceTrendService:
    """绩效趋势分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_engineer_trend(
        self,
        engineer_id: int,
        periods: int = 6
    ) -> Dict[str, Any]:
        """
        获取工程师历史趋势

        Args:
            engineer_id: 工程师ID
            periods: 历史周期数（默认6个）

        Returns:
            趋势数据
        """
        results = self.db.query(PerformanceResult).join(
            PerformancePeriod, PerformanceResult.period_id == PerformancePeriod.id
        ).filter(
            PerformanceResult.user_id == engineer_id
        ).order_by(
            desc(PerformancePeriod.start_date)
        ).limit(periods).all()

        if not results:
            return {
                'engineer_id': engineer_id,
                'periods': [],
                'total_scores': [],
                'ranks': [],
                'levels': [],
                'dimension_trends': {},
                'has_data': False
            }

        # 反转顺序（从最早到最新）
        results = list(reversed(results))

        trend_data = {
            'engineer_id': engineer_id,
            'periods': [],
            'total_scores': [],
            'ranks': [],
            'levels': [],
            'dimension_trends': {
                'technical': [],
                'execution': [],
                'cost_quality': [],
                'knowledge': [],
                'collaboration': []
            },
            'has_data': True
        }

        for result in results:
            trend_data['periods'].append({
                'period_id': result.period_id,
                'period_name': result.period.period_name if result.period else '',
                'start_date': result.period.start_date.isoformat() if result.period else '',
                'end_date': result.period.end_date.isoformat() if result.period else ''
            })
            trend_data['total_scores'].append(float(result.total_score or 0))
            trend_data['ranks'].append(result.company_rank or 0)
            trend_data['levels'].append(result.level or 'D')
            
            # 五维得分（从indicator_scores获取，如果没有则使用默认值）
            if result.indicator_scores:
                scores = result.indicator_scores
                trend_data['dimension_trends']['technical'].append(float(scores.get('technical_score', 75)))
                trend_data['dimension_trends']['execution'].append(float(scores.get('execution_score', 75)))
                trend_data['dimension_trends']['cost_quality'].append(float(scores.get('cost_quality_score', 75)))
                trend_data['dimension_trends']['knowledge'].append(float(scores.get('knowledge_score', 75)))
                trend_data['dimension_trends']['collaboration'].append(float(scores.get('collaboration_score', 75)))
            else:
                # 使用默认值
                trend_data['dimension_trends']['technical'].append(75.0)
                trend_data['dimension_trends']['execution'].append(75.0)
                trend_data['dimension_trends']['cost_quality'].append(75.0)
                trend_data['dimension_trends']['knowledge'].append(75.0)
                trend_data['dimension_trends']['collaboration'].append(75.0)

        # 计算趋势指标
        if len(trend_data['total_scores']) >= 2:
            recent_scores = trend_data['total_scores'][-3:]  # 最近3个周期
            earlier_scores = trend_data['total_scores'][:3]  # 前3个周期
            
            recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            earlier_avg = sum(earlier_scores) / len(earlier_scores) if earlier_scores else 0
            
            trend_data['trend_analysis'] = {
                'score_trend': 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable',
                'score_change': round(recent_avg - earlier_avg, 2),
                'recent_avg': round(recent_avg, 2),
                'earlier_avg': round(earlier_avg, 2)
            }

        return trend_data

    def identify_ability_changes(
        self,
        engineer_id: int,
        periods: int = 6
    ) -> List[Dict[str, Any]]:
        """
        识别能力变化

        Returns:
            能力变化分析列表
        """
        trend_data = self.get_engineer_trend(engineer_id, periods)

        if not trend_data.get('has_data') or len(trend_data['total_scores']) < 2:
            return []

        changes = []
        dimension_names = {
            'technical': '技术能力',
            'execution': '项目执行',
            'cost_quality': '成本/质量',
            'knowledge': '知识沉淀',
            'collaboration': '团队协作'
        }

        for dim, scores in trend_data['dimension_trends'].items():
            if len(scores) >= 2:
                recent_avg = sum(scores[-3:]) / min(3, len(scores))
                earlier_avg = sum(scores[:3]) / min(3, len(scores))
                change = recent_avg - earlier_avg

                if abs(change) > 5:  # 变化超过5分
                    changes.append({
                        'dimension': dim,
                        'dimension_name': dimension_names[dim],
                        'change': round(change, 2),
                        'trend': 'improving' if change > 0 else 'declining',
                        'recent_avg': round(recent_avg, 2),
                        'earlier_avg': round(earlier_avg, 2),
                        'change_percentage': round(change / earlier_avg * 100, 1) if earlier_avg > 0 else 0
                    })

        return changes

    def get_department_trend(
        self,
        department_id: int,
        periods: int = 6
    ) -> Dict[str, Any]:
        """
        获取部门整体趋势

        Args:
            department_id: 部门ID
            periods: 历史周期数

        Returns:
            部门趋势数据
        """
        # 获取部门所有工程师
        from app.models.user import User
        from app.models.organization import Employee
        
        employees = self.db.query(Employee).filter(
            Employee.department_id == department_id
        ).all()
        
        employee_ids = [e.id for e in employees]
        user_ids = [
            u.id for u in self.db.query(User).filter(
                User.employee_id.in_(employee_ids)
            ).all()
        ]

        if not user_ids:
            return {
                'department_id': department_id,
                'has_data': False
            }

        # 获取最近的周期
        recent_periods = self.db.query(PerformancePeriod).order_by(
            desc(PerformancePeriod.end_date)
        ).limit(periods).all()

        if not recent_periods:
            return {
                'department_id': department_id,
                'has_data': False
            }

        period_ids = [p.id for p in recent_periods]

        # 统计每个周期的平均分
        period_stats = []
        for period in reversed(recent_periods):  # 从最早到最新
            results = self.db.query(PerformanceResult).filter(
                PerformanceResult.period_id == period.id,
                PerformanceResult.user_id.in_(user_ids)
            ).all()

            if results:
                scores = [float(r.total_score or 0) for r in results]
                period_stats.append({
                    'period_id': period.id,
                    'period_name': period.period_name,
                    'avg_score': round(sum(scores) / len(scores), 2),
                    'engineer_count': len(results),
                    'max_score': round(max(scores), 2),
                    'min_score': round(min(scores), 2)
                })

        return {
            'department_id': department_id,
            'has_data': True,
            'period_stats': period_stats,
            'trend': self._calculate_trend([s['avg_score'] for s in period_stats]) if period_stats else 'stable',
            'total_periods': len(period_stats)
        }

    def compare_departments(
        self,
        department_ids: List[int],
        period_id: int
    ) -> Dict[str, Any]:
        """
        对比多个部门的趋势

        Args:
            department_ids: 部门ID列表
            period_id: 考核周期ID

        Returns:
            部门对比数据
        """
        comparison = {
            'period_id': period_id,
            'departments': []
        }
        
        for dept_id in department_ids:
            dept_trend = self.get_department_trend(dept_id, periods=6)
            if dept_trend.get('has_data'):
                comparison['departments'].append({
                    'department_id': dept_id,
                    'trend_data': dept_trend
                })
        
        return comparison

    def _calculate_trend(self, scores: List[float]) -> str:
        """计算趋势方向"""
        if len(scores) < 2:
            return 'stable'
        
        recent_avg = sum(scores[-3:]) / min(3, len(scores))
        earlier_avg = sum(scores[:3]) / min(3, len(scores))
        
        if recent_avg > earlier_avg + 2:
            return 'improving'
        elif recent_avg < earlier_avg - 2:
            return 'declining'
        else:
            return 'stable'
