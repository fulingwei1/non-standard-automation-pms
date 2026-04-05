# -*- coding: utf-8 -*-
"""
评分阈值配置

将销售模块中的硬编码评分阈值集中管理，支持通过环境变量覆盖。

使用方法：
    from app.core.scoring_config import scoring_config

    if lead.score >= scoring_config.LEAD_SCORE_HIGH:
        # 高分线索处理
        ...

环境变量配置示例：
    SCORING_LEAD_SCORE_HIGH=85
    SCORING_OPP_WIN_RATE_HIGH=0.75
"""

import os
from decimal import Decimal
from functools import lru_cache


class ScoringConfig:
    """
    评分阈值配置类

    所有阈值支持通过环境变量覆盖，环境变量前缀为 SCORING_
    """

    # ==================== 线索评分阈值 ====================

    # 高分线索阈值（≥此值视为高质量线索）
    LEAD_SCORE_HIGH: int = 80
    # 中分线索阈值（≥此值且<高分视为中等线索）
    LEAD_SCORE_MEDIUM: int = 50
    # 低分线索阈值（<此值视为低质量线索）
    LEAD_SCORE_LOW: int = 30

    # ==================== 商机赢率阈值 ====================

    # 高赢率阈值（≥此值视为高概率成交）
    OPP_WIN_RATE_HIGH: float = 0.7
    # 中赢率阈值
    OPP_WIN_RATE_MEDIUM: float = 0.4
    # 低赢率阈值
    OPP_WIN_RATE_LOW: float = 0.2

    # ==================== 技术评估阈值 ====================

    # 技术评估通过阈值
    TECH_ASSESSMENT_PASS: int = 60
    # 技术评估优秀阈值
    TECH_ASSESSMENT_EXCELLENT: int = 85

    # ==================== 客户评分阈值 ====================

    # 优质客户阈值
    CUSTOMER_SCORE_PREMIUM: int = 85
    # 良好客户阈值
    CUSTOMER_SCORE_GOOD: int = 70
    # 一般客户阈值
    CUSTOMER_SCORE_NORMAL: int = 50

    # ==================== 项目健康度阈值 ====================

    # 健康项目阈值
    PROJECT_HEALTH_GOOD: int = 80
    # 警告阈值
    PROJECT_HEALTH_WARNING: int = 60
    # 危险阈值
    PROJECT_HEALTH_DANGER: int = 40

    # ==================== 毛利率阈值 ====================

    # 标准毛利率（%）
    MARGIN_STANDARD: float = 35.0
    # 警告毛利率（%）
    MARGIN_WARNING: float = 25.0
    # 预警毛利率（%）
    MARGIN_ALERT: float = 20.0
    # 最低毛利率（%）
    MARGIN_MINIMUM: float = 15.0

    # ==================== 优先级评分权重 ====================

    # 金额权重
    PRIORITY_WEIGHT_AMOUNT: float = 0.3
    # 赢率权重
    PRIORITY_WEIGHT_WIN_RATE: float = 0.25
    # 紧急度权重
    PRIORITY_WEIGHT_URGENCY: float = 0.25
    # 战略价值权重
    PRIORITY_WEIGHT_STRATEGIC: float = 0.2

    def __init__(self):
        """从环境变量加载配置覆盖"""
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        for attr_name in dir(self):
            # 跳过私有属性和方法
            if attr_name.startswith("_") or callable(getattr(self, attr_name)):
                continue

            env_key = f"SCORING_{attr_name}"
            env_value = os.getenv(env_key)

            if env_value is not None:
                try:
                    current_value = getattr(self, attr_name)
                    # 根据原始类型转换
                    if isinstance(current_value, int):
                        setattr(self, attr_name, int(env_value))
                    elif isinstance(current_value, float):
                        setattr(self, attr_name, float(env_value))
                    elif isinstance(current_value, Decimal):
                        setattr(self, attr_name, Decimal(env_value))
                except (ValueError, TypeError):
                    pass  # 保持默认值

    def get_lead_level(self, score: int) -> str:
        """
        根据分数获取线索级别

        Returns:
            HIGH / MEDIUM / LOW
        """
        if score >= self.LEAD_SCORE_HIGH:
            return "HIGH"
        elif score >= self.LEAD_SCORE_MEDIUM:
            return "MEDIUM"
        else:
            return "LOW"

    def get_win_rate_level(self, rate: float) -> str:
        """
        根据赢率获取级别

        Args:
            rate: 0-1 之间的赢率值

        Returns:
            HIGH / MEDIUM / LOW
        """
        if rate >= self.OPP_WIN_RATE_HIGH:
            return "HIGH"
        elif rate >= self.OPP_WIN_RATE_MEDIUM:
            return "MEDIUM"
        else:
            return "LOW"

    def get_margin_level(self, margin: float) -> str:
        """
        根据毛利率获取预警级别

        Args:
            margin: 毛利率百分比（如 25.0 表示 25%）

        Returns:
            NORMAL / WARNING / ALERT / CRITICAL
        """
        if margin >= self.MARGIN_STANDARD:
            return "NORMAL"
        elif margin >= self.MARGIN_WARNING:
            return "WARNING"
        elif margin >= self.MARGIN_ALERT:
            return "ALERT"
        else:
            return "CRITICAL"

    def get_project_health_level(self, score: int) -> str:
        """
        根据健康度分数获取级别

        Returns:
            GOOD / WARNING / DANGER
        """
        if score >= self.PROJECT_HEALTH_GOOD:
            return "GOOD"
        elif score >= self.PROJECT_HEALTH_WARNING:
            return "WARNING"
        else:
            return "DANGER"

    def calculate_priority_score(
        self,
        amount_score: float,
        win_rate_score: float,
        urgency_score: float,
        strategic_score: float,
    ) -> float:
        """
        计算综合优先级分数

        Args:
            amount_score: 金额分数 (0-100)
            win_rate_score: 赢率分数 (0-100)
            urgency_score: 紧急度分数 (0-100)
            strategic_score: 战略价值分数 (0-100)

        Returns:
            综合优先级分数 (0-100)
        """
        return (
            amount_score * self.PRIORITY_WEIGHT_AMOUNT
            + win_rate_score * self.PRIORITY_WEIGHT_WIN_RATE
            + urgency_score * self.PRIORITY_WEIGHT_URGENCY
            + strategic_score * self.PRIORITY_WEIGHT_STRATEGIC
        )


@lru_cache()
def get_scoring_config() -> ScoringConfig:
    """
    获取评分配置单例

    使用 lru_cache 确保全局只有一个实例
    """
    return ScoringConfig()


# 全局配置实例（便捷访问）
scoring_config = get_scoring_config()
