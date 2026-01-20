# -*- coding: utf-8 -*-
"""
等级确定模块
提供优先级、重要性、紧急程度等级的确定功能
"""


class LevelDeterminationMixin:
    """等级确定功能混入类"""

    def _determine_priority_level(self, total_score: int, urgency_score: int) -> str:
        """确定优先级等级"""
        if total_score >= 80 and urgency_score >= 8:
            return "P1"  # 重要且紧急
        elif total_score >= 70:
            return "P2"  # 重要但不紧急
        elif urgency_score >= 8:
            return "P3"  # 不重要但紧急
        else:
            return "P4"  # 不重要且不紧急

    def _determine_importance_level(self, total_score: int) -> str:
        """确定重要程度"""
        if total_score >= 80:
            return "HIGH"
        elif total_score >= 60:
            return "MEDIUM"
        else:
            return "LOW"

    def _determine_urgency_level(self, urgency_score: int) -> str:
        """确定紧急程度"""
        if urgency_score >= 8:
            return "HIGH"
        elif urgency_score >= 5:
            return "MEDIUM"
        else:
            return "LOW"
