"""
Comprehensive tests for alert rule engine services.
Tests coverage for:
- app.services.alert_rule_engine (AlertRuleEngine class and components)
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.alert import AlertRule, AlertRecord
from app.models.enums import AlertLevelEnum
from app.services.alert_rule_engine import (
    AlertRuleEngine,
    AlertRuleEngineBase,
    ConditionEvaluator,
    LevelDeterminer,
    AlertCreator,
    AlertUpgrader,
    RuleManager,
)


class TestAlertRuleEngineInit:
    """Test AlertRuleEngine initialization."""

    def test_init_with_db_session(self):
        """Test that AlertRuleEngine can be initialized with a db session."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)
        assert engine is not None

    def test_engine_has_evaluate_rule(self):
        """Test that engine has evaluate_rule method."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)
        assert hasattr(engine, 'evaluate_rule')

    def test_engine_has_check_condition(self):
        """Test that engine has check_condition method."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)
        assert hasattr(engine, 'check_condition')

    def test_engine_has_should_create_alert(self):
        """Test that engine has should_create_alert method."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)
        assert hasattr(engine, 'should_create_alert')

    def test_engine_has_create_alert(self):
        """Test that engine has create_alert method."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)
        assert hasattr(engine, 'create_alert')

    def test_engine_has_upgrade_alert(self):
        """Test that engine has upgrade_alert method."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)
        assert hasattr(engine, 'upgrade_alert')

    def test_engine_has_level_priority(self):
        """Test that engine has level_priority method."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)
        assert hasattr(engine, 'level_priority')


class TestEvaluateRule:
    """Test evaluate_rule method."""

    def test_evaluate_rule_disabled_rule(self):
        """Test that disabled rules return None."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)

        mock_rule = MagicMock()
        mock_rule.is_enabled = False

        result = engine.evaluate_rule(mock_rule, {})
        assert result is None

    def test_evaluate_rule_condition_not_met(self):
        """Test that rules with unmet conditions return None."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)

        mock_rule = MagicMock()
        mock_rule.is_enabled = True

        with patch.object(engine, 'check_condition', return_value=False):
            result = engine.evaluate_rule(mock_rule, {"health": "H1"})
            assert result is None

    def test_evaluate_rule_creates_alert(self):
        """Test that rules with met conditions create alerts."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)

        mock_rule = MagicMock()
        mock_rule.is_enabled = True
        mock_alert = MagicMock()

        with patch.object(engine, 'check_condition', return_value=True), \
             patch.object(LevelDeterminer, 'determine_alert_level', return_value='WARNING'), \
             patch.object(engine, 'should_create_alert', return_value=None), \
             patch.object(engine, 'create_alert', return_value=mock_alert):
            result = engine.evaluate_rule(mock_rule, {"health": "H2"})
            assert result == mock_alert

    def test_evaluate_rule_upgrades_existing(self):
        """Test that existing lower-level alerts get upgraded."""
        mock_db = MagicMock(spec=Session)
        engine = AlertRuleEngine(mock_db)

        mock_rule = MagicMock()
        mock_rule.is_enabled = True
        existing_alert = MagicMock()
        existing_alert.alert_level = 'WARNING'
        upgraded_alert = MagicMock()

        with patch.object(engine, 'check_condition', return_value=True), \
             patch.object(LevelDeterminer, 'determine_alert_level', return_value='CRITICAL'), \
             patch.object(engine, 'should_create_alert', return_value=existing_alert), \
             patch.object(engine, 'level_priority', side_effect=lambda x: {'WARNING': 1, 'CRITICAL': 3}.get(x, 0)), \
             patch.object(engine, 'upgrade_alert', return_value=upgraded_alert):
            result = engine.evaluate_rule(mock_rule, {"health": "H3"})
            assert result == upgraded_alert


class TestConditionEvaluator:
    """Test ConditionEvaluator component."""

    def test_condition_evaluator_exists(self):
        """Test that ConditionEvaluator class exists."""
        assert ConditionEvaluator is not None

    def test_condition_evaluator_has_check_condition(self):
        """Test that ConditionEvaluator has check_condition."""
        assert hasattr(ConditionEvaluator, 'check_condition')


class TestLevelDeterminer:
    """Test LevelDeterminer component."""

    def test_level_determiner_exists(self):
        """Test that LevelDeterminer class exists."""
        assert LevelDeterminer is not None

    def test_determine_alert_level_exists(self):
        """Test that determine_alert_level method exists."""
        assert hasattr(LevelDeterminer, 'determine_alert_level')


class TestAlertCreatorComponent:
    """Test AlertCreator component."""

    def test_alert_creator_exists(self):
        """Test that AlertCreator class exists."""
        assert AlertCreator is not None


class TestAlertUpgraderComponent:
    """Test AlertUpgrader component."""

    def test_alert_upgrader_exists(self):
        """Test that AlertUpgrader class exists."""
        assert AlertUpgrader is not None


class TestRuleManagerComponent:
    """Test RuleManager component."""

    def test_rule_manager_exists(self):
        """Test that RuleManager class exists."""
        assert RuleManager is not None

    def test_get_or_create_rule_exists(self):
        """Test that get_or_create_rule method exists."""
        assert hasattr(RuleManager, 'get_or_create_rule')


class TestAlertLevelEnum:
    """Test AlertLevelEnum values."""

    def test_info_level(self):
        """Test INFO level exists."""
        assert AlertLevelEnum.INFO is not None

    def test_warning_level(self):
        """Test WARNING level exists."""
        assert AlertLevelEnum.WARNING is not None

    def test_critical_level(self):
        """Test CRITICAL level exists."""
        assert AlertLevelEnum.CRITICAL is not None

    def test_urgent_level(self):
        """Test URGENT level exists."""
        assert AlertLevelEnum.URGENT is not None
