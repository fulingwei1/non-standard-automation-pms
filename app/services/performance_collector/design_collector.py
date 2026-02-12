# -*- coding: utf-8 -*-
"""
工程师绩效数据采集 - 设计评审和调试问题数据收集
"""

from datetime import date
from typing import Any, Dict


from app.models.engineer_performance import DesignReview, MechanicalDebugIssue, TestBugRecord
from .base import PerformanceDataCollectorBase


class DesignCollector(PerformanceDataCollectorBase):
    """设计评审和调试问题数据收集器"""

    def collect_design_review_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集设计评审数据（机械工程师，增强版：包含异常处理）"""
        try:
            reviews = self.db.query(DesignReview).filter(
                DesignReview.designer_id == engineer_id,
                DesignReview.review_date.between(start_date, end_date)
            ).all()

            if not reviews:
                return {
                    'total_reviews': 0,
                    'first_pass_reviews': 0,
                    'first_pass_rate': 0.0
                }

            total_reviews = len(reviews)
            first_pass_reviews = sum(1 for r in reviews if r.is_first_pass)
            first_pass_rate = (first_pass_reviews / total_reviews * 100) if total_reviews > 0 else 0.0

            return {
                'total_reviews': total_reviews,
                'first_pass_reviews': first_pass_reviews,
                'first_pass_rate': round(first_pass_rate, 2)
            }
        except Exception as e:
            return {
                'total_reviews': 0,
                'first_pass_reviews': 0,
                'first_pass_rate': 0.0,
                'error': str(e)
            }

    def collect_debug_issue_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集调试问题数据（增强版：包含异常处理）"""
        try:
            # 机械调试问题
            mechanical_issues = self.db.query(MechanicalDebugIssue).filter(
                MechanicalDebugIssue.responsible_id == engineer_id,
                MechanicalDebugIssue.found_date.between(start_date, end_date)
            ).all()

            # 测试Bug记录
            test_bugs = self.db.query(TestBugRecord).filter(
                TestBugRecord.assignee_id == engineer_id,
                TestBugRecord.found_time.between(start_date, end_date)
            ).all()

            # 计算平均修复时长
            resolved_bugs = [b for b in test_bugs if b.status in ('resolved', 'closed')]
            fix_times = [float(b.fix_duration_hours) for b in resolved_bugs if b.fix_duration_hours]
            avg_fix_time = sum(fix_times) / len(fix_times) if fix_times else 0.0

            return {
                'mechanical_issues': len(mechanical_issues),
                'test_bugs': len(test_bugs),
                'resolved_bugs': len(resolved_bugs),
                'avg_fix_time': round(avg_fix_time, 2)
            }
        except Exception as e:
            return {
                'mechanical_issues': 0,
                'test_bugs': 0,
                'resolved_bugs': 0,
                'avg_fix_time': 0.0,
                'error': str(e)
            }
