# -*- coding: utf-8 -*-
"""
评分配置测试
"""
import pytest
import os
from unittest.mock import patch
from app.core.scoring_config import ScoringConfig, get_scoring_config, scoring_config


class TestScoringConfig:
    """测试 ScoringConfig 类"""

    def test_default_lead_score_thresholds(self):
        """测试默认线索评分阈值"""
        config = ScoringConfig()
        assert config.LEAD_SCORE_HIGH == 80
        assert config.LEAD_SCORE_MEDIUM == 50
        assert config.LEAD_SCORE_LOW == 30

    def test_default_win_rate_thresholds(self):
        """测试默认赢率阈值"""
        config = ScoringConfig()
        assert config.OPP_WIN_RATE_HIGH == 0.7
        assert config.OPP_WIN_RATE_MEDIUM == 0.4
        assert config.OPP_WIN_RATE_LOW == 0.2

    def test_default_tech_assessment_thresholds(self):
        """测试默认技术评估阈值"""
        config = ScoringConfig()
        assert config.TECH_ASSESSMENT_PASS == 60
        assert config.TECH_ASSESSMENT_EXCELLENT == 85

    def test_default_customer_score_thresholds(self):
        """测试默认客户评分阈值"""
        config = ScoringConfig()
        assert config.CUSTOMER_SCORE_PREMIUM == 85
        assert config.CUSTOMER_SCORE_GOOD == 70
        assert config.CUSTOMER_SCORE_NORMAL == 50

    def test_default_project_health_thresholds(self):
        """测试默认项目健康度阈值"""
        config = ScoringConfig()
        assert config.PROJECT_HEALTH_GOOD == 80
        assert config.PROJECT_HEALTH_WARNING == 60
        assert config.PROJECT_HEALTH_DANGER == 40

    def test_default_margin_thresholds(self):
        """测试默认毛利率阈值"""
        config = ScoringConfig()
        assert config.MARGIN_STANDARD == 35.0
        assert config.MARGIN_WARNING == 25.0
        assert config.MARGIN_ALERT == 20.0
        assert config.MARGIN_MINIMUM == 15.0

    def test_default_priority_weights(self):
        """测试默认优先级权重"""
        config = ScoringConfig()
        assert config.PRIORITY_WEIGHT_AMOUNT == 0.3
        assert config.PRIORITY_WEIGHT_WIN_RATE == 0.25
        assert config.PRIORITY_WEIGHT_URGENCY == 0.25
        assert config.PRIORITY_WEIGHT_STRATEGIC == 0.2


class TestScoringConfigEnvOverride:
    """测试环境变量覆盖"""

    @patch.dict(os.environ, {"SCORING_LEAD_SCORE_HIGH": "90"})
    def test_env_override_int(self):
        """测试整数类型环境变量覆盖"""
        # 清除缓存以获取新实例
        get_scoring_config.cache_clear()
        config = get_scoring_config()
        assert config.LEAD_SCORE_HIGH == 90
        get_scoring_config.cache_clear()

    @patch.dict(os.environ, {"SCORING_OPP_WIN_RATE_HIGH": "0.85"})
    def test_env_override_float(self):
        """测试浮点类型环境变量覆盖"""
        get_scoring_config.cache_clear()
        config = get_scoring_config()
        assert config.OPP_WIN_RATE_HIGH == 0.85
        get_scoring_config.cache_clear()


class TestGetLeadLevel:
    """测试 get_lead_level 方法"""

    def test_high_level(self):
        """高分线索"""
        config = ScoringConfig()
        assert config.get_lead_level(90) == "HIGH"
        assert config.get_lead_level(80) == "HIGH"

    def test_medium_level(self):
        """中等线索"""
        config = ScoringConfig()
        assert config.get_lead_level(60) == "MEDIUM"
        assert config.get_lead_level(50) == "MEDIUM"

    def test_low_level(self):
        """低分线索"""
        config = ScoringConfig()
        assert config.get_lead_level(40) == "LOW"
        assert config.get_lead_level(10) == "LOW"

    def test_boundary_high_medium(self):
        """边界测试 - 高分和中分"""
        config = ScoringConfig()
        assert config.get_lead_level(79) == "MEDIUM"
        assert config.get_lead_level(80) == "HIGH"

    def test_boundary_medium_low(self):
        """边界测试 - 中分和低分"""
        config = ScoringConfig()
        assert config.get_lead_level(49) == "LOW"
        assert config.get_lead_level(50) == "MEDIUM"


class TestGetWinRateLevel:
    """测试 get_win_rate_level 方法"""

    def test_high_win_rate(self):
        """高赢率"""
        config = ScoringConfig()
        assert config.get_win_rate_level(0.9) == "HIGH"
        assert config.get_win_rate_level(0.7) == "HIGH"

    def test_medium_win_rate(self):
        """中赢率"""
        config = ScoringConfig()
        assert config.get_win_rate_level(0.5) == "MEDIUM"
        assert config.get_win_rate_level(0.4) == "MEDIUM"

    def test_low_win_rate(self):
        """低赢率"""
        config = ScoringConfig()
        assert config.get_win_rate_level(0.2) == "LOW"
        assert config.get_win_rate_level(0.1) == "LOW"


class TestGetMarginLevel:
    """测试 get_margin_level 方法"""

    def test_normal_margin(self):
        """正常毛利率"""
        config = ScoringConfig()
        assert config.get_margin_level(40.0) == "NORMAL"
        assert config.get_margin_level(35.0) == "NORMAL"

    def test_warning_margin(self):
        """警告毛利率"""
        config = ScoringConfig()
        assert config.get_margin_level(30.0) == "WARNING"
        assert config.get_margin_level(25.0) == "WARNING"

    def test_alert_margin(self):
        """预警毛利率"""
        config = ScoringConfig()
        assert config.get_margin_level(22.0) == "ALERT"
        assert config.get_margin_level(20.0) == "ALERT"

    def test_critical_margin(self):
        """危险毛利率"""
        config = ScoringConfig()
        assert config.get_margin_level(18.0) == "CRITICAL"
        assert config.get_margin_level(10.0) == "CRITICAL"


class TestGetProjectHealthLevel:
    """测试 get_project_health_level 方法"""

    def test_good_health(self):
        """健康项目"""
        config = ScoringConfig()
        assert config.get_project_health_level(90) == "GOOD"
        assert config.get_project_health_level(80) == "GOOD"

    def test_warning_health(self):
        """警告项目"""
        config = ScoringConfig()
        assert config.get_project_health_level(70) == "WARNING"
        assert config.get_project_health_level(60) == "WARNING"

    def test_danger_health(self):
        """危险项目"""
        config = ScoringConfig()
        assert config.get_project_health_level(50) == "DANGER"
        assert config.get_project_health_level(30) == "DANGER"


class TestCalculatePriorityScore:
    """测试 calculate_priority_score 方法"""

    def test_priority_calculation(self):
        """测试优先级计算"""
        config = ScoringConfig()
        # 默认权重: amount=0.3, win_rate=0.25, urgency=0.25, strategic=0.2
        score = config.calculate_priority_score(
            amount_score=100,
            win_rate_score=80,
            urgency_score=60,
            strategic_score=40,
        )
        expected = 100 * 0.3 + 80 * 0.25 + 60 * 0.25 + 40 * 0.2
        assert score == expected

    def test_priority_calculation_zero(self):
        """测试全零分数"""
        config = ScoringConfig()
        score = config.calculate_priority_score(
            amount_score=0,
            win_rate_score=0,
            urgency_score=0,
            strategic_score=0,
        )
        assert score == 0

    def test_priority_calculation_max(self):
        """测试满分"""
        config = ScoringConfig()
        score = config.calculate_priority_score(
            amount_score=100,
            win_rate_score=100,
            urgency_score=100,
            strategic_score=100,
        )
        assert score == 100


class TestScoringConfigSingleton:
    """测试单例模式"""

    def test_singleton_same_instance(self):
        """测试返回相同实例"""
        get_scoring_config.cache_clear()
        config1 = get_scoring_config()
        config2 = get_scoring_config()
        assert config1 is config2
        get_scoring_config.cache_clear()

    def test_global_instance_type(self):
        """测试全局实例类型"""
        get_scoring_config.cache_clear()
        config = get_scoring_config()
        assert isinstance(config, ScoringConfig)
        get_scoring_config.cache_clear()