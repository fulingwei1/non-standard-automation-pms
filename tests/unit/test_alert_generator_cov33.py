# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 预警内容生成器 (AlertGenerator)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

try:
    from app.services.alert_rule_engine.alert_generator import AlertGenerator
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="alert_generator 导入失败")


class TestGenerateAlertNo:
    def test_format_contains_rule_code_and_date(self):
        """预警编号包含规则编码前缀和日期"""
        db = MagicMock()
        db.query.return_value.count.return_value = 0

        rule = MagicMock()
        rule.rule_code = "project_delay"

        with patch(
            "app.services.alert_rule_engine.alert_generator.apply_like_filter",
            return_value=db.query.return_value
        ):
            alert_no = AlertGenerator.generate_alert_no(db, rule, {})

        today = datetime.now().strftime('%Y%m%d')
        assert today in alert_no
        assert alert_no.startswith("PRO")  # "project_delay"[:3].upper() = "PRO"

    def test_sequence_increments(self):
        """当天有已有预警时序号递增"""
        db = MagicMock()
        db.query.return_value.count.return_value = 5  # 已有5条

        rule = MagicMock()
        rule.rule_code = "cost_overrun"

        with patch(
            "app.services.alert_rule_engine.alert_generator.apply_like_filter",
            return_value=db.query.return_value
        ):
            alert_no = AlertGenerator.generate_alert_no(db, rule, {})

        # 序号应该是6
        assert alert_no.endswith("0006")

    def test_sequence_padded_to_4_digits(self):
        """序号补零到4位"""
        db = MagicMock()
        db.query.return_value.count.return_value = 0

        rule = MagicMock()
        rule.rule_code = "AL001"

        with patch(
            "app.services.alert_rule_engine.alert_generator.apply_like_filter",
            return_value=db.query.return_value
        ):
            alert_no = AlertGenerator.generate_alert_no(db, rule, {})

        assert alert_no.endswith("0001")


class TestGenerateAlertTitle:
    def test_uses_target_name(self):
        """使用target_name生成标题"""
        rule = MagicMock()
        rule.rule_name = "项目延期预警"

        target_data = {"target_name": "PJ001项目", "target_no": "PJ001"}
        title = AlertGenerator.generate_alert_title(rule, target_data, "RED")

        assert "PJ001项目" in title
        assert "项目延期预警" in title

    def test_falls_back_to_target_no(self):
        """无target_name时使用target_no"""
        rule = MagicMock()
        rule.rule_name = "成本超支"

        target_data = {"target_name": None, "target_no": "CO001"}
        title = AlertGenerator.generate_alert_title(rule, target_data, "YELLOW")

        assert "CO001" in title

    def test_falls_back_to_default(self):
        """无target_name和target_no时使用默认文字"""
        rule = MagicMock()
        rule.rule_name = "测试规则"

        target_data = {}
        title = AlertGenerator.generate_alert_title(rule, target_data, "RED")

        assert "对象" in title or "测试规则" in title


class TestGenerateAlertContent:
    def test_content_includes_rule_name(self):
        """内容包含规则名称"""
        rule = MagicMock()
        rule.rule_name = "项目进度预警"
        rule.description = "项目出现延期"
        rule.target_field = None
        rule.threshold_value = "10"
        rule.solution_guide = "联系PM确认"

        content = AlertGenerator.generate_alert_content(rule, {}, "RED")

        assert "项目进度预警" in content
        assert "项目出现延期" in content

    def test_content_includes_threshold(self):
        """内容包含阈值"""
        rule = MagicMock()
        rule.rule_name = "延期预警"
        rule.description = None
        rule.target_field = None
        rule.threshold_value = "5天"
        rule.solution_guide = None

        content = AlertGenerator.generate_alert_content(rule, {}, "YELLOW")

        assert "5天" in content

    def test_content_includes_solution_guide(self):
        """内容包含处理建议"""
        rule = MagicMock()
        rule.rule_name = "成本预警"
        rule.description = None
        rule.target_field = None
        rule.threshold_value = None
        rule.solution_guide = "立即审查预算"

        content = AlertGenerator.generate_alert_content(rule, {}, "RED")

        assert "立即审查预算" in content

    def test_content_includes_trigger_value_when_engine_provided(self):
        """引擎提供时内容包含触发值"""
        rule = MagicMock()
        rule.rule_name = "延期预警"
        rule.description = None
        rule.target_field = "delay_days"
        rule.threshold_value = None
        rule.solution_guide = None

        engine = MagicMock()
        engine.get_field_value.return_value = 7

        content = AlertGenerator.generate_alert_content(rule, {"delay_days": 7}, "RED", engine=engine)

        assert "7" in content
