# -*- coding: utf-8 -*-
"""
评分配置单元测试
"""

import os
import pytest
from decimal import Decimal


class TestScoringConfigDefaults:
    """测试默认阈值配置"""

    def test_lead_score_thresholds(self):
        """测试线索评分阈值"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.LEAD_SCORE_HIGH == 80
        assert config.LEAD_SCORE_MEDIUM == 50
        assert config.LEAD_SCORE_LOW == 30

    def test_win_rate_thresholds(self):
        """测试赢率阈值"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.OPP_WIN_RATE_HIGH == 0.7
        assert config.OPP_WIN_RATE_MEDIUM == 0.4
        assert config.OPP_WIN_RATE_LOW == 0.2

    def test_tech_assessment_thresholds(self):
        """测试技术评估阈值"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.TECH_ASSESSMENT_PASS == 60
        assert config.TECH_ASSESSMENT_EXCELLENT == 85

    def test_customer_score_thresholds(self):
        """测试客户评分阈值"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.CUSTOMER_SCORE_PREMIUM == 85
        assert config.CUSTOMER_SCORE_GOOD == 70
        assert config.CUSTOMER_SCORE_NORMAL == 50

    def test_project_health_thresholds(self):
        """测试项目健康度阈值"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.PROJECT_HEALTH_GOOD == 80
        assert config.PROJECT_HEALTH_WARNING == 60
        assert config.PROJECT_HEALTH_DANGER == 40

    def test_margin_thresholds(self):
        """测试毛利率阈值"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.MARGIN_STANDARD == 35.0
        assert config.MARGIN_WARNING == 25.0
        assert config.MARGIN_ALERT == 20.0
        assert config.MARGIN_MINIMUM == 15.0

    def test_priority_weights(self):
        """测试优先级权重"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.PRIORITY_WEIGHT_AMOUNT == 0.3
        assert config.PRIORITY_WEIGHT_WIN_RATE == 0.25
        assert config.PRIORITY_WEIGHT_URGENCY == 0.25
        assert config.PRIORITY_WEIGHT_STRATEGIC == 0.2


class TestScoringConfigGetLevel:
    """测试评分级别判断"""

    def test_get_lead_level_high(self):
        """测试高分线索"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_lead_level(85) == "HIGH"
        assert config.get_lead_level(80) == "HIGH"

    def test_get_lead_level_medium(self):
        """测试中等线索"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_lead_level(60) == "MEDIUM"
        assert config.get_lead_level(50) == "MEDIUM"

    def test_get_lead_level_low(self):
        """测试低分线索"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_lead_level(30) == "LOW"
        assert config.get_lead_level(10) == "LOW"

    def test_get_win_rate_level_high(self):
        """测试高赢率"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_win_rate_level(0.8) == "HIGH"
        assert config.get_win_rate_level(0.7) == "HIGH"

    def test_get_win_rate_level_medium(self):
        """测试中等赢率"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_win_rate_level(0.5) == "MEDIUM"
        assert config.get_win_rate_level(0.4) == "MEDIUM"

    def test_get_win_rate_level_low(self):
        """测试低赢率"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_win_rate_level(0.2) == "LOW"
        assert config.get_win_rate_level(0.1) == "LOW"

    def test_get_margin_level_normal(self):
        """测试正常毛利率"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_margin_level(35.0) == "NORMAL"
        assert config.get_margin_level(40.0) == "NORMAL"

    def test_get_margin_level_warning(self):
        """测试警告毛利率"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_margin_level(28.0) == "WARNING"
        assert config.get_margin_level(25.0) == "WARNING"

    def test_get_margin_level_alert(self):
        """测试预警毛利率"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_margin_level(22.0) == "ALERT"
        assert config.get_margin_level(20.0) == "ALERT"

    def test_get_margin_level_critical(self):
        """测试危险毛利率"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_margin_level(15.0) == "CRITICAL"
        assert config.get_margin_level(10.0) == "CRITICAL"

    def test_get_project_health_level_good(self):
        """测试健康项目"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_project_health_level(90) == "GOOD"
        assert config.get_project_health_level(80) == "GOOD"

    def test_get_project_health_level_warning(self):
        """测试警告项目"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_project_health_level(70) == "WARNING"
        assert config.get_project_health_level(60) == "WARNING"

    def test_get_project_health_level_danger(self):
        """测试危险项目"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        assert config.get_project_health_level(40) == "DANGER"
        assert config.get_project_health_level(20) == "DANGER"


class TestScoringConfigCalculatePriority:
    """测试优先级计算"""

    def test_calculate_priority_score_basic(self):
        """测试基本优先级计算"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        score = config.calculate_priority_score(
            amount_score=100,
            win_rate_score=80,
            urgency_score=60,
            strategic_score=40,
        )
        # 100*0.3 + 80*0.25 + 60*0.25 + 40*0.2 = 30+20+15+8=73
        assert score == 73

    def test_calculate_priority_score_zeros(self):
        """测试全零分数"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        score = config.calculate_priority_score(
            amount_score=0,
            win_rate_score=0,
            urgency_score=0,
            strategic_score=0,
        )
        assert score == 0

    def test_calculate_priority_score_max(self):
        """测试满分"""
        from app.core.scoring_config import ScoringConfig

        config = ScoringConfig()
        score = config.calculate_priority_score(
            amount_score=100,
            win_rate_score=100,
            urgency_score=100,
            strategic_score=100,
        )
        # 100*0.3 + 100*0.25 + 100*0.25 + 100*0.2 = 30+25+25+20=100
        assert score == 100


class TestScoringConfigEnvOverride:
    """测试环境变量覆盖"""

    def test_env_override_int(self):
        """测试整数环境变量覆盖"""
        os.environ["SCORING_LEAD_SCORE_HIGH"] = "90"
        try:
            from app.core.scoring_config import get_scoring_config

            # 清除缓存
            get_scoring_config.cache_clear()
            config = get_scoring_config()
            assert config.LEAD_SCORE_HIGH == 90
        finally:
            os.environ.pop("SCORING_LEAD_SCORE_HIGH", None)
            get_scoring_config.cache_clear()

    def test_env_override_float(self):
        """测试浮点数环境变量覆盖"""
        os.environ["SCORING_OPP_WIN_RATE_HIGH"] = "0.8"
        try:
            from app.core.scoring_config import get_scoring_config

            get_scoring_config.cache_clear()
            config = get_scoring_config()
            assert config.OPP_WIN_RATE_HIGH == 0.8
        finally:
            os.environ.pop("SCORING_OPP_WIN_RATE_HIGH", None)
            get_scoring_config.cache_clear()


class TestScoringConfigSingleton:
    """测试单例模式"""

    def test_get_scoring_config_returns_same_instance(self):
        """测试返回同一实例"""
        from app.core.scoring_config import get_scoring_config

        config1 = get_scoring_config()
        config2 = get_scoring_config()
        assert config1 is config2