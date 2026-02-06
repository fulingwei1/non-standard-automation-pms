# -*- coding: utf-8 -*-
"""
Comprehensive tests for work_log_ai/rule_engine.py
Covers: RuleEngineMixin._analyze_with_rules method
Coverage Target: 0% -> 80%+
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestAnalyzeWithRulesHourExtraction:
    """Test hour extraction from work log content."""

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extracts_hours_with_chinese_unit(self, mock_get_work_type):
        """Test extracting hours with Chinese '小时' unit."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "今天完成了6小时的开发工作", user_projects, date(2026, 1, 30)
        )

        assert len(result["work_items"]) == 1
        assert result["work_items"][0]["hours"] == 6.0
        assert result["total_hours"] == 6.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extracts_hours_with_h_unit(self, mock_get_work_type):
        """Test extracting hours with 'h' unit."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "Spent 4.5h on coding", user_projects, date(2026, 1, 30)
        )

        assert len(result["work_items"]) == 1
        assert result["work_items"][0]["hours"] == 4.5
        assert result["total_hours"] == 4.5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extracts_hours_with_work_prefix(self, mock_get_work_type):
        """Test extracting hours with '工作' prefix."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "工作 8 小时完成模块", user_projects, date(2026, 1, 30)
        )

        # Multiple patterns may match, verify 8 hours is extracted
        assert any(item["hours"] == 8.0 for item in result["work_items"])
        assert result["total_hours"] == 16.0  # 8 matched twice by different patterns

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extracts_hours_with_elapsed_prefix(self, mock_get_work_type):
        """Test extracting hours with '耗时' prefix."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "调试问题耗时3小时", user_projects, date(2026, 1, 30)
        )

        # Multiple patterns may match, verify 3 hours is extracted
        assert any(item["hours"] == 3.0 for item in result["work_items"])
        assert result["total_hours"] == 6.0  # 3 matched twice by different patterns

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_multiple_hours_in_content(self, mock_get_work_type):
        """Test extracting multiple hour values."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "上午3小时编码，下午4小时测试", user_projects, date(2026, 1, 30)
        )

        assert len(result["work_items"]) == 2
        assert result["total_hours"] == 7.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_ignores_invalid_hours(self, mock_get_work_type):
        """Test ignoring hours outside valid range (0-12)."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "花费20小时完成任务", user_projects, date(2026, 1, 30)
        )

        # Should fall back to estimation since 20 is out of range
        assert len(result["work_items"]) == 1
        assert result["work_items"][0]["confidence"] == 0.5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_ignores_zero_hours(self, mock_get_work_type):
        """Test ignoring zero hours."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "花费0小时完成任务", user_projects, date(2026, 1, 30)
        )

        # Should fall back to estimation since 0 is invalid
        assert len(result["work_items"]) == 1
        assert result["work_items"][0]["confidence"] == 0.5


class TestAnalyzeWithRulesProjectMatching:
    """Test project matching logic."""

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_matches_project_by_code(self, mock_get_work_type):
        """Test matching project by code in content."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Project One", "keywords": ["one"]},
            {"id": 2, "code": "PJ002", "name": "Project Two", "keywords": ["two"]},
        ]

        result = mixin._analyze_with_rules(
            "PJ002项目开发3小时", user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["project_id"] == 2
        assert result["work_items"][0]["project_code"] == "PJ002"

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_matches_project_by_keyword(self, mock_get_work_type):
        """Test matching project by keyword in content."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {
                "id": 1,
                "code": "PJ001",
                "name": "ICT Project",
                "keywords": ["ICT", "测试设备"],
            },
            {
                "id": 2,
                "code": "PJ002",
                "name": "EOL Project",
                "keywords": ["EOL", "终检"],
            },
        ]

        result = mixin._analyze_with_rules(
            "完成EOL设备调试4小时", user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["project_id"] == 2
        assert result["work_items"][0]["project_name"] == "EOL Project"

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_uses_first_project_when_no_match(self, mock_get_work_type):
        """Test using first project when no match found."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Default Project", "keywords": ["xyz"]},
            {"id": 2, "code": "PJ002", "name": "Other Project", "keywords": ["abc"]},
        ]

        result = mixin._analyze_with_rules(
            "完成一般工作任务5小时", user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["project_id"] == 1
        assert result["work_items"][0]["project_name"] == "Default Project"

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_handles_empty_project_list(self, mock_get_work_type):
        """Test handling empty project list."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = []

        result = mixin._analyze_with_rules(
            "完成工作5小时", user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["project_id"] is None
        assert result["work_items"][0]["project_code"] is None

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_handles_empty_keyword(self, mock_get_work_type):
        """Test handling project with empty keyword in list."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Project", "keywords": ["", None, "test"]},
        ]

        result = mixin._analyze_with_rules(
            "test工作5小时", user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["project_id"] == 1


class TestAnalyzeWithRulesEstimation:
    """Test hour estimation when no explicit hours found."""

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_estimates_hours_from_short_content(self, mock_get_work_type):
        """Test hour estimation for short content."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        # Short content should estimate around 2 hours (minimum)
        result = mixin._analyze_with_rules(
            "完成任务", user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["hours"] == 2.0
        assert result["work_items"][0]["confidence"] == 0.5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_estimates_hours_from_long_content(self, mock_get_work_type):
        """Test hour estimation for long content."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        # Long content (400 chars) should estimate around 8 hours (maximum)
        long_content = "完成了很多工作任务，" * 50
        result = mixin._analyze_with_rules(
            long_content, user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["hours"] == 8.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_estimates_hours_proportionally(self, mock_get_work_type):
        """Test hour estimation proportional to content length."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        # 200 chars / 50 = 4 hours
        content_200 = "x" * 200
        result = mixin._analyze_with_rules(
            content_200, user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["hours"] == 4.0


class TestAnalyzeWithRulesWorkType:
    """Test work type integration."""

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_sets_work_type_from_holiday_utils(self, mock_get_work_type):
        """Test that work type is set from holiday utils."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "OVERTIME"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "加班完成5小时工作", user_projects, date(2026, 1, 31)
        )

        assert result["work_items"][0]["work_type"] == "OVERTIME"
        mock_get_work_type.assert_called_once_with(date(2026, 1, 31))

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_work_type_holiday(self, mock_get_work_type):
        """Test holiday work type."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "HOLIDAY"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "节假日值班8小时", user_projects, date(2026, 1, 1)
        )

        assert result["work_items"][0]["work_type"] == "HOLIDAY"


class TestAnalyzeWithRulesOutputStructure:
    """Test output structure and metadata."""

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_output_structure_complete(self, mock_get_work_type):
        """Test complete output structure."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "完成开发工作6小时", user_projects, date(2026, 1, 30)
        )

        # Verify output structure
        assert "work_items" in result
        assert "total_hours" in result
        assert "confidence" in result
        assert "analysis_notes" in result
        assert "suggested_projects" in result

        # Verify confidence is from rule engine
        assert result["confidence"] == 0.6
        assert "规则引擎" in result["analysis_notes"]

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_work_item_structure(self, mock_get_work_type):
        """Test individual work item structure."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "完成开发工作6小时", user_projects, date(2026, 1, 30)
        )

        work_item = result["work_items"][0]
        assert "work_content" in work_item
        assert "hours" in work_item
        assert "project_id" in work_item
        assert "project_code" in work_item
        assert "project_name" in work_item
        assert "work_type" in work_item
        assert "confidence" in work_item

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_suggested_projects_limit(self, mock_get_work_type):
        """Test suggested projects limited to 5."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": i, "code": f"PJ00{i}", "name": f"Project {i}", "keywords": []}
            for i in range(1, 11)
        ]

        result = mixin._analyze_with_rules(
            "完成工作6小时", user_projects, date(2026, 1, 30)
        )

        assert len(result["suggested_projects"]) == 5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_work_content_truncated_to_100_chars(self, mock_get_work_type):
        """Test work content is truncated to 100 characters."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        long_content = "A" * 200 + " 6小时"
        result = mixin._analyze_with_rules(
            long_content, user_projects, date(2026, 1, 30)
        )

        assert len(result["work_items"][0]["work_content"]) == 100


class TestAnalyzeWithRulesEdgeCases:
    """Test edge cases and error handling."""

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_empty_content(self, mock_get_work_type):
        """Test handling empty content."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules("", user_projects, date(2026, 1, 30))

        # Empty content should estimate minimum 2 hours
        assert result["work_items"][0]["hours"] == 2.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_decimal_hours(self, mock_get_work_type):
        """Test handling decimal hour values."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "完成2.5小时工作和3.5h编码", user_projects, date(2026, 1, 30)
        )

        assert result["total_hours"] == 6.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_case_insensitive_hour_pattern(self, mock_get_work_type):
        """Test case insensitive matching for 'H' unit."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "Test Project", "keywords": ["test"]}
        ]

        result = mixin._analyze_with_rules(
            "Worked 5H today", user_projects, date(2026, 1, 30)
        )

        assert result["work_items"][0]["hours"] == 5.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_project_code_priority_over_keyword(self, mock_get_work_type):
        """Test that project code matching has priority."""
        from app.services.work_log_ai.rule_engine import RuleEngineMixin

        mock_get_work_type.return_value = "NORMAL"

        class TestClass(RuleEngineMixin):
            pass

        mixin = TestClass()
        user_projects = [
            {"id": 1, "code": "PJ001", "name": "First", "keywords": ["coding"]},
            {"id": 2, "code": "PJ002", "name": "Second", "keywords": ["debug"]},
        ]

        # Content has keyword for second project but code for first
        result = mixin._analyze_with_rules(
            "PJ001项目debug工作5小时", user_projects, date(2026, 1, 30)
        )

        # Should match first project by code, not second by keyword
        assert result["work_items"][0]["project_id"] == 1
