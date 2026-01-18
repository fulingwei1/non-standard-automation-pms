# -*- coding: utf-8 -*-
"""
人员智能匹配服务
功能：AI驱动的人员智能匹配，实现6维度加权匹配算法

向后兼容：保持原有的类接口
"""

from .base import StaffMatchingBase
from .candidate_management import CandidateManager
from .matching import MatchingEngine
from .profile_aggregation import ProfileAggregator
from .score_calculators import (
    AttitudeScoreCalculator,
    DomainScoreCalculator,
    QualityScoreCalculator,
    SkillScoreCalculator,
    SpecialScoreCalculator,
    WorkloadScoreCalculator,
)


class StaffMatchingService(StaffMatchingBase):
    """人员智能匹配服务 - 统一接口类"""

    # 继承基类的配置
    DIMENSION_WEIGHTS = StaffMatchingBase.DIMENSION_WEIGHTS
    PRIORITY_THRESHOLDS = StaffMatchingBase.PRIORITY_THRESHOLDS

    # 委托给匹配引擎
    match_candidates = MatchingEngine.match_candidates
    _get_candidate_employees = MatchingEngine._get_candidate_employees
    _calculate_candidate_scores = MatchingEngine._calculate_candidate_scores

    # 委托给档案聚合器
    aggregate_employee_profile = ProfileAggregator.aggregate_employee_profile
    update_employee_workload = ProfileAggregator.update_employee_workload

    # 委托给候选人管理器
    accept_candidate = CandidateManager.accept_candidate
    reject_candidate = CandidateManager.reject_candidate
    get_matching_history = CandidateManager.get_matching_history

    # 保留原有的计算方法（向后兼容，实际调用计算器）
    @classmethod
    def _calculate_skill_score(cls, db, employee_id, profile, required_skills, preferred_skills):
        """计算技能匹配分（向后兼容方法）"""
        return SkillScoreCalculator.calculate_skill_score(
            db, employee_id, profile, required_skills, preferred_skills
        )

    @classmethod
    def _calculate_domain_score(cls, db, employee_id, profile, required_domains):
        """计算领域匹配分（向后兼容方法）"""
        return DomainScoreCalculator.calculate_domain_score(
            db, employee_id, profile, required_domains
        )

    @classmethod
    def _calculate_attitude_score(cls, db, employee_id, profile, required_attitudes):
        """计算态度评分（向后兼容方法）"""
        return AttitudeScoreCalculator.calculate_attitude_score(
            db, employee_id, profile, required_attitudes
        )

    @classmethod
    def _calculate_quality_score(cls, db, employee_id):
        """计算质量评分（向后兼容方法）"""
        return QualityScoreCalculator.calculate_quality_score(db, employee_id)

    @classmethod
    def _calculate_workload_score(cls, profile, required_allocation):
        """计算工作负载分（向后兼容方法）"""
        return WorkloadScoreCalculator.calculate_workload_score(profile, required_allocation)

    @classmethod
    def _calculate_special_score(cls, db, employee_id, profile):
        """计算特殊能力分（向后兼容方法）"""
        return SpecialScoreCalculator.calculate_special_score(db, employee_id, profile)


# 向后兼容：导出主服务类
__all__ = [
    'StaffMatchingService',
    # 基类
    'StaffMatchingBase',
    # 匹配引擎
    'MatchingEngine',
    # 档案聚合器
    'ProfileAggregator',
    # 候选人管理器
    'CandidateManager',
    # 得分计算器
    'SkillScoreCalculator',
    'DomainScoreCalculator',
    'AttitudeScoreCalculator',
    'QualityScoreCalculator',
    'WorkloadScoreCalculator',
    'SpecialScoreCalculator',
]
