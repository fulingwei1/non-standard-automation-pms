# -*- coding: utf-8 -*-
"""
风险计算工具

提供标准化的风险等级计算函数，避免代码重复。
"""
from typing import Literal, Optional

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Probability = Literal["LOW", "MEDIUM", "HIGH"]
Impact = Literal["LOW", "MEDIUM", "HIGH"]


def calculate_risk_level(
    probability: Optional[str],
    impact: Optional[str]
) -> Optional[str]:
    """
    基于概率和影响计算风险等级

    使用标准风险矩阵：
    ┌─────────────┬─────┬────────┬──────┐
    │ 概率 \\ 影响 │ LOW │ MEDIUM │ HIGH │
    ├─────────────┼─────┼────────┼──────┤
    │ HIGH        │ MED │ HIGH   │ CRIT │
    │ MEDIUM      │ LOW │ MEDIUM │ HIGH │
    │ LOW         │ LOW │ LOW    │ MED  │
    └─────────────┴─────┴────────┴──────┘

    计算规则：
    - CRITICAL: 概率HIGH + 影响HIGH
    - HIGH: 概率HIGH 或 影响HIGH（但非两者同时）
    - MEDIUM: 概率MEDIUM 或 影响MEDIUM
    - LOW: 其他情况

    Args:
        probability: 发生概率 (LOW/MEDIUM/HIGH)
        impact: 影响程度 (LOW/MEDIUM/HIGH)

    Returns:
        风险等级 (LOW/MEDIUM/HIGH/CRITICAL)，如果输入为空则返回None

    Examples:
        >>> calculate_risk_level("HIGH", "HIGH")
        'CRITICAL'
        >>> calculate_risk_level("HIGH", "MEDIUM")
        'HIGH'
        >>> calculate_risk_level("MEDIUM", "LOW")
        'MEDIUM'
        >>> calculate_risk_level("LOW", "LOW")
        'LOW'
    """
    # 处理空值
    if not probability or not impact:
        return None

    # 标准化为大写
    probability = probability.upper()
    impact = impact.upper()

    # 应用风险矩阵规则
    if probability == "HIGH" and impact == "HIGH":
        return "CRITICAL"
    elif probability == "HIGH" or impact == "HIGH":
        return "HIGH"
    elif probability == "MEDIUM" or impact == "MEDIUM":
        return "MEDIUM"
    else:
        return "LOW"


def get_risk_score(risk_level: str) -> int:
    """
    将风险等级转换为数值分数

    用于风险排序和统计分析。

    Args:
        risk_level: 风险等级 (LOW/MEDIUM/HIGH/CRITICAL)

    Returns:
        风险分数 (1-4)

    Examples:
        >>> get_risk_score("CRITICAL")
        4
        >>> get_risk_score("LOW")
        1
    """
    risk_scores = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }
    return risk_scores.get(risk_level.upper(), 0)


def compare_risk_levels(old_level: str, new_level: str) -> str:
    """
    比较两个风险等级，判断���升级、降级还是不变

    Args:
        old_level: 原风险等级
        new_level: 新风险等级

    Returns:
        "UPGRADE" | "DOWNGRADE" | "UNCHANGED"

    Examples:
        >>> compare_risk_levels("MEDIUM", "HIGH")
        'UPGRADE'
        >>> compare_risk_levels("HIGH", "MEDIUM")
        'DOWNGRADE'
        >>> compare_risk_levels("HIGH", "HIGH")
        'UNCHANGED'
    """
    old_score = get_risk_score(old_level)
    new_score = get_risk_score(new_level)

    if new_score > old_score:
        return "UPGRADE"
    elif new_score < old_score:
        return "DOWNGRADE"
    else:
        return "UNCHANGED"


class RiskCalculator:
    """风险计算器类（封装函数式API，供测试和OOP场景使用）"""

    @staticmethod
    def calculate_risk_level(probability: Optional[str], impact: Optional[str]) -> Optional[str]:
        return calculate_risk_level(probability, impact)

    @staticmethod
    def compare_risk_levels(level1: Optional[str], level2: Optional[str]) -> int:
        return compare_risk_levels(level1, level2)

    @staticmethod
    def get_risk_score(risk_level: Optional[str]) -> int:
        return get_risk_score(risk_level)
