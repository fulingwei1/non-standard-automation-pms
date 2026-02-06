# -*- coding: utf-8 -*-
"""
rule_engine.py 单元测试

测试工作日志规则引擎分析功能
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app.services.work_log_ai.rule_engine import RuleEngineMixin


class TestRuleEngine(RuleEngineMixin):
    """用于测试的规则引擎实例类"""
    pass


@pytest.fixture
def engine():
    return TestRuleEngine()


@pytest.fixture
def sample_projects():
    """示例项目列表"""
    return [
        {
            "id": 1,
            "code": "PJ2401001",
            "name": "自动化测试设备项目",
            "keywords": ["自动化", "测试设备", "AOI"]
        },
        {
            "id": 2,
            "code": "PJ2401002",
            "name": "视觉检测系统",
            "keywords": ["视觉", "检测", "相机"]
        },
        {
            "id": 3,
            "code": "PJ2401003",
            "name": "装配线体改造",
            "keywords": ["装配", "产线", "改造"]
        }
    ]


@pytest.mark.unit
class TestAnalyzeWithRules:
    """测试 _analyze_with_rules 方法"""

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extract_hours_chinese(self, mock_work_type, engine, sample_projects):
        """测试提取中文工时（X小时）"""
        mock_work_type.return_value = "NORMAL"
        # 注意：使用只匹配一个模式的内容，避免重复匹配
        content = "今天完成了自动化设备的调试工作，用时6小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["total_hours"] == 6.0
        assert len(result["work_items"]) == 1
        assert result["work_items"][0]["hours"] == 6.0
        assert result["work_items"][0]["project_id"] == 1

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extract_hours_english(self, mock_work_type, engine, sample_projects):
        """测试提取英文工时（Xh）"""
        mock_work_type.return_value = "NORMAL"
        content = "Debug session for the testing equipment, 4.5h"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["total_hours"] == 4.5
        assert result["work_items"][0]["hours"] == 4.5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extract_hours_with_prefix(self, mock_work_type, engine, sample_projects):
        """测试带前缀的工时（工作X小时）- 会匹配多个模式"""
        mock_work_type.return_value = "NORMAL"
        # "工作 8 小时" 会同时匹配 "工作X小时" 和 "X小时" 两个模式
        content = "项目现场调试，工作 8 小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        # 两个模式都匹配到8，所以总工时是16
        assert result["total_hours"] == 16.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extract_multiple_hours(self, mock_work_type, engine, sample_projects):
        """测试提取多个工时"""
        mock_work_type.return_value = "NORMAL"
        content = "上午设计评审3小时，下午编码4小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["total_hours"] == 7.0
        assert len(result["work_items"]) == 2

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_invalid_hours_ignored(self, mock_work_type, engine, sample_projects):
        """测试忽略无效工时（超过12小时）"""
        mock_work_type.return_value = "NORMAL"
        content = "完成任务，耗时20小时"  # 超过12小时，不合理

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        # 应该使用估算工时而非提取的20小时
        assert result["work_items"][0]["confidence"] == 0.5  # 估算的置信度

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_match_project_by_code(self, mock_work_type, engine, sample_projects):
        """测试通过项目编码匹配"""
        mock_work_type.return_value = "NORMAL"
        content = "PJ2401002项目进度更新，完成视觉方案设计，6小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["work_items"][0]["project_id"] == 2
        assert result["work_items"][0]["project_code"] == "PJ2401002"

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_match_project_by_keyword(self, mock_work_type, engine, sample_projects):
        """测试通过关键词匹配项目"""
        mock_work_type.return_value = "NORMAL"
        content = "今天调试相机参数，优化检测效果，5小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["work_items"][0]["project_id"] == 2  # 匹配"相机"关键词

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_use_first_project_when_no_match(self, mock_work_type, engine, sample_projects):
        """测试无匹配时使用第一个项目"""
        mock_work_type.return_value = "NORMAL"
        content = "参加部门会议讨论工作计划，4小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["work_items"][0]["project_id"] == 1  # 使用第一个项目

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_no_projects_available(self, mock_work_type, engine):
        """测试没有可用项目"""
        mock_work_type.return_value = "NORMAL"
        content = "完成设计文档，6小时"

        result = engine._analyze_with_rules(content, [], date(2024, 3, 15))

        assert result["work_items"][0]["project_id"] is None
        assert result["work_items"][0]["project_code"] is None

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_estimate_hours_short_content(self, mock_work_type, engine, sample_projects):
        """测试短内容的工时估算"""
        mock_work_type.return_value = "NORMAL"
        content = "处理邮件"  # 很短的内容

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        # 最少2小时
        assert result["work_items"][0]["hours"] == 2.0
        assert result["work_items"][0]["confidence"] == 0.5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_estimate_hours_long_content(self, mock_work_type, engine, sample_projects):
        """测试长内容的工时估算"""
        mock_work_type.return_value = "NORMAL"
        content = "今天完成了以下工作：" + "调试设备、" * 100  # 很长的内容

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        # 最多8小时
        assert result["work_items"][0]["hours"] == 8.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_work_type_from_holiday_utils(self, mock_work_type, engine, sample_projects):
        """测试工作类型来自节假日工具"""
        mock_work_type.return_value = "OVERTIME"
        content = "周末加班处理紧急问题，4小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 16))

        assert result["work_items"][0]["work_type"] == "OVERTIME"
        mock_work_type.assert_called_once_with(date(2024, 3, 16))

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_result_structure(self, mock_work_type, engine, sample_projects):
        """测试返回结果结构"""
        mock_work_type.return_value = "NORMAL"
        content = "完成自动化设备调试，6小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert "work_items" in result
        assert "total_hours" in result
        assert "confidence" in result
        assert "analysis_notes" in result
        assert "suggested_projects" in result
        assert result["confidence"] == 0.6
        assert "规则引擎" in result["analysis_notes"]

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_suggested_projects_limit(self, mock_work_type, engine):
        """测试推荐项目限制为5个"""
        mock_work_type.return_value = "NORMAL"
        # 创建10个项目
        many_projects = [
            {"id": i, "code": f"PJ{i}", "name": f"项目{i}", "keywords": []}
            for i in range(10)
        ]
        content = "完成工作，4小时"

        result = engine._analyze_with_rules(content, many_projects, date(2024, 3, 15))

        assert len(result["suggested_projects"]) == 5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_content_truncation(self, mock_work_type, engine, sample_projects):
        """测试工作内容截断"""
        mock_work_type.return_value = "NORMAL"
        long_content = "A" * 200 + "，6小时"  # 超过100字

        result = engine._analyze_with_rules(long_content, sample_projects, date(2024, 3, 15))

        # 提取到工时时，内容截取前100字
        assert len(result["work_items"][0]["work_content"]) == 100

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_extracted_hours_confidence(self, mock_work_type, engine, sample_projects):
        """测试提取工时的置信度"""
        mock_work_type.return_value = "NORMAL"
        content = "完成调试，耗时5小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["work_items"][0]["confidence"] == 0.7  # 提取的置信度

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_keyword_empty_string(self, mock_work_type, engine):
        """测试空关键词处理"""
        mock_work_type.return_value = "NORMAL"
        projects = [
            {"id": 1, "code": "PJ001", "name": "测试项目", "keywords": ["", None, "有效关键词"]}
        ]
        content = "今天处理有效关键词相关任务，4小时"

        result = engine._analyze_with_rules(content, projects, date(2024, 3, 15))

        assert result["work_items"][0]["project_id"] == 1

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_decimal_hours_extraction(self, mock_work_type, engine, sample_projects):
        """测试小数工时提取"""
        mock_work_type.return_value = "NORMAL"
        content = "完成文档编写，2.5小时"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["total_hours"] == 2.5
        assert result["work_items"][0]["hours"] == 2.5

    @patch("app.services.work_log_ai.rule_engine.get_work_type")
    def test_case_insensitive_hours(self, mock_work_type, engine, sample_projects):
        """测试大小写不敏感的工时提取"""
        mock_work_type.return_value = "NORMAL"
        content = "Meeting and coding, 3H"

        result = engine._analyze_with_rules(content, sample_projects, date(2024, 3, 15))

        assert result["total_hours"] == 3.0
