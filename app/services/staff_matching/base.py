# -*- coding: utf-8 -*-
"""
人员智能匹配服务 - 基础配置和工具方法
"""

from app.models.staff_matching import RecommendationTypeEnum


class StaffMatchingBase:
    """人员匹配服务基类 - 包含配置和工具方法"""

    # 维度权重配置
    DIMENSION_WEIGHTS = {
        'skill': 0.30,      # 技能匹配 30%
        'domain': 0.15,     # 领域匹配 15%
        'attitude': 0.20,   # 态度评分 20%
        'quality': 0.15,    # 质量评分 15%
        'workload': 0.15,   # 工作负载 15%
        'special': 0.05     # 特殊能力 5%
    }

    # 优先级对应的最低分阈值
    PRIORITY_THRESHOLDS = {
        'P1': 85,  # 最高优先级
        'P2': 75,
        'P3': 65,
        'P4': 55,
        'P5': 50   # 最低优先级
    }

    @classmethod
    def get_priority_threshold(cls, priority: str) -> int:
        """获取优先级对应的最低分阈值"""
        return cls.PRIORITY_THRESHOLDS.get(priority, 65)

    @classmethod
    def classify_recommendation(cls, total_score: float, threshold: int) -> str:
        """根据得分和阈值分类推荐类型"""
        if total_score >= threshold + 15:
            return RecommendationTypeEnum.STRONG.value
        elif total_score >= threshold:
            return RecommendationTypeEnum.RECOMMENDED.value
        elif total_score >= threshold - 10:
            return RecommendationTypeEnum.ACCEPTABLE.value
        else:
            return RecommendationTypeEnum.WEAK.value
