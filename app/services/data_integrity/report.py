# -*- coding: utf-8 -*-
"""
数据质量报告模块
提供数据质量报告的生成功能
"""

from typing import Any, Dict, Optional

from app.models.engineer_performance import EngineerProfile
from app.models.performance import PerformancePeriod


class DataReportMixin:
    """数据质量报告功能混入类"""

    def generate_data_quality_report(
        self,
        period_id: int,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成数据质量报告

        Args:
            period_id: 考核周期ID
            department_id: 部门ID（可选，如果指定则只统计该部门）

        Returns:
            数据质量报告
        """
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        # 获取工程师列表
        query = self.db.query(EngineerProfile)
        if department_id:
            from app.models.organization import Employee
            from app.models.user import User
            employees = self.db.query(Employee).filter(
                Employee.department_id == department_id
            ).all()
            employee_ids = [e.id for e in employees]
            user_ids = [
                u.id for u in self.db.query(User).filter(
                    User.employee_id.in_(employee_ids)
                ).all()
            ]
            query = query.filter(EngineerProfile.user_id.in_(user_ids))

        engineers = query.all()

        total_engineers = len(engineers)
        if total_engineers == 0:
            return {
                'period_id': period_id,
                'department_id': department_id,
                'total_engineers': 0,
                'reports': []
            }

        reports = []
        completeness_scores = []

        for engineer in engineers:
            report = self.check_data_completeness(engineer.user_id, period_id)
            reports.append(report)
            completeness_scores.append(report['completeness_score'])

        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0

        # 统计缺失项
        all_missing = []
        all_warnings = []
        for report in reports:
            all_missing.extend(report['missing_items'])
            all_warnings.extend(report['warnings'])

        missing_summary = {}
        for item in all_missing:
            missing_summary[item] = missing_summary.get(item, 0) + 1

        warnings_summary = {}
        for item in all_warnings:
            warnings_summary[item] = warnings_summary.get(item, 0) + 1

        return {
            'period_id': period_id,
            'department_id': department_id,
            'total_engineers': total_engineers,
            'average_completeness_score': round(avg_completeness, 2),
            'missing_items_summary': missing_summary,
            'warnings_summary': warnings_summary,
            'reports': reports
        }
