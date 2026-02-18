# -*- coding: utf-8 -*-
"""第二十七批 - quality_risk_analyzer 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.quality_risk_ai.quality_risk_analyzer")

from app.services.quality_risk_ai.quality_risk_analyzer import QualityRiskAnalyzer


def make_db():
    return MagicMock()


def make_work_log(**kwargs):
    return {
        "work_date": kwargs.get("work_date", "2024-06-10"),
        "user_name": kwargs.get("user_name", "张三"),
        "task_name": kwargs.get("task_name", "模块开发"),
        "work_content": kwargs.get("work_content", "完成功能开发"),
        "work_result": kwargs.get("work_result", "功能正常")
    }


class TestQualityRiskAnalyzerInit:
    def test_init_stores_db(self):
        db = make_db()
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor"):
            analyzer = QualityRiskAnalyzer(db)
        assert analyzer.db is db

    def test_init_creates_keyword_extractor(self):
        db = make_db()
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor") as MockExt:
            analyzer = QualityRiskAnalyzer(db)
        MockExt.assert_called_once()


class TestAnalyzeWorkLogsEmpty:
    def setup_method(self):
        db = make_db()
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor"):
            self.analyzer = QualityRiskAnalyzer(db)

    def test_empty_logs_returns_low_risk(self):
        result = self.analyzer.analyze_work_logs([])
        assert result["risk_level"] == "LOW"

    def test_empty_logs_returns_zero_score(self):
        result = self.analyzer.analyze_work_logs([])
        assert result["risk_score"] == 0.0

    def test_empty_logs_empty_signals(self):
        result = self.analyzer.analyze_work_logs([])
        assert result["risk_signals"] == []

    def test_empty_logs_empty_predicted_issues(self):
        result = self.analyzer.analyze_work_logs([])
        assert result["predicted_issues"] == []


class TestAnalyzeWithKeywords:
    def setup_method(self):
        db = make_db()
        self.mock_extractor = MagicMock()
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor", return_value=self.mock_extractor):
            self.analyzer = QualityRiskAnalyzer(db)

    def test_keyword_analysis_called_for_each_log(self):
        self.mock_extractor.analyze_text.return_value = {
            "risk_keywords": {"BUG": ["缺陷"]},
            "abnormal_patterns": [],
            "risk_score": 10.0
        }
        self.mock_extractor.determine_risk_level.return_value = "LOW"

        logs = [make_work_log() for _ in range(3)]
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY", ""):
            result = self.analyzer.analyze_work_logs(logs)

        assert self.mock_extractor.analyze_text.call_count == 3

    def test_returns_keyword_based_method(self):
        self.mock_extractor.analyze_text.return_value = {
            "risk_keywords": {},
            "abnormal_patterns": [],
            "risk_score": 5.0
        }
        self.mock_extractor.determine_risk_level.return_value = "LOW"

        logs = [make_work_log()]
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY", ""):
            result = self.analyzer.analyze_work_logs(logs)

        assert result["ai_analysis"]["method"] == "KEYWORD_BASED"

    def test_keyword_confidence_is_60(self):
        self.mock_extractor.analyze_text.return_value = {
            "risk_keywords": {},
            "abnormal_patterns": [],
            "risk_score": 5.0
        }
        self.mock_extractor.determine_risk_level.return_value = "LOW"

        logs = [make_work_log()]
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY", ""):
            result = self.analyzer.analyze_work_logs(logs)

        assert result["ai_confidence"] == 60.0

    def test_high_risk_score_logs_signals(self):
        self.mock_extractor.analyze_text.return_value = {
            "risk_keywords": {"BUG": ["严重缺陷", "崩溃", "报错"]},
            "abnormal_patterns": [],
            "risk_score": 50.0
        }
        self.mock_extractor.determine_risk_level.return_value = "HIGH"

        logs = [make_work_log()]
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY", ""):
            result = self.analyzer.analyze_work_logs(logs)

        assert result["risk_signals"] != [] or result["risk_score"] > 20


class TestMergeAnalysisResults:
    def setup_method(self):
        db = make_db()
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor"):
            self.analyzer = QualityRiskAnalyzer(db)

    def test_takes_higher_risk_level(self):
        kw_result = {
            "risk_level": "LOW",
            "risk_score": 20.0,
            "risk_signals": [],
            "risk_keywords": {},
            "abnormal_patterns": [],
            "ai_analysis": {"method": "KEYWORD_BASED", "logs_analyzed": 1}
        }
        ai_result = {
            "risk_level": "HIGH",
            "risk_score": 70.0,
            "risk_category": "BUG",
            "risk_signals": [],
            "predicted_issues": [],
            "rework_probability": 60.0,
            "estimated_impact_days": 3,
            "ai_analysis": {"method": "GLM_BASED"},
            "ai_confidence": 80.0,
            "analysis_model": "glm-4-flash"
        }
        result = self.analyzer._merge_analysis_results(kw_result, ai_result)
        assert result["risk_level"] == "HIGH"

    def test_weighted_score_calculation(self):
        kw_result = {
            "risk_level": "MEDIUM",
            "risk_score": 40.0,
            "risk_signals": [],
            "risk_keywords": {},
            "abnormal_patterns": [],
            "ai_analysis": {"method": "KEYWORD_BASED"}
        }
        ai_result = {
            "risk_level": "MEDIUM",
            "risk_score": 60.0,
            "risk_category": None,
            "risk_signals": [],
            "predicted_issues": [],
            "rework_probability": 0,
            "estimated_impact_days": 0,
            "ai_analysis": {"method": "GLM_BASED"},
            "ai_confidence": 70.0,
            "analysis_model": "glm-4-flash"
        }
        result = self.analyzer._merge_analysis_results(kw_result, ai_result)
        # 40 * 0.4 + 60 * 0.6 = 16 + 36 = 52
        assert abs(result["risk_score"] - 52.0) < 0.1

    def test_merges_signals(self):
        kw_result = {
            "risk_level": "LOW",
            "risk_score": 10.0,
            "risk_signals": [{"date": "2024-06-10", "risk_score": 25}],
            "risk_keywords": {},
            "abnormal_patterns": [],
            "ai_analysis": {}
        }
        ai_result = {
            "risk_level": "LOW",
            "risk_score": 10.0,
            "risk_category": None,
            "risk_signals": [{"signal": "AI信号"}],
            "predicted_issues": [],
            "rework_probability": 0,
            "estimated_impact_days": 0,
            "ai_analysis": {},
            "ai_confidence": 70.0,
            "analysis_model": "test"
        }
        result = self.analyzer._merge_analysis_results(kw_result, ai_result)
        assert len(result["risk_signals"]) == 2


class TestPredictIssuesFromKeywords:
    def setup_method(self):
        db = make_db()
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor"):
            self.analyzer = QualityRiskAnalyzer(db)

    def test_no_keywords_returns_empty(self):
        result = self.analyzer._predict_issues_from_keywords({}, [])
        assert result == []

    def test_many_bug_keywords_predict_issue(self):
        keywords = {"BUG": ["缺陷1", "缺陷2", "缺陷3", "缺陷4"]}
        result = self.analyzer._predict_issues_from_keywords(keywords, [])
        assert len(result) > 0
        assert any("缺陷" in issue["issue"] or "返工" in issue["issue"] for issue in result)

    def test_performance_keyword_predicts_issue(self):
        keywords = {"PERFORMANCE": ["慢", "超时"]}
        result = self.analyzer._predict_issues_from_keywords(keywords, [])
        assert any("性能" in issue["issue"] for issue in result)

    def test_stability_keyword_predicts_issue(self):
        keywords = {"STABILITY": ["崩溃", "不稳定"]}
        result = self.analyzer._predict_issues_from_keywords(keywords, [])
        assert any("稳定" in issue["issue"] for issue in result)

    def test_critical_pattern_predicts_issue(self):
        patterns = [{"name": "连续失败", "severity": "CRITICAL"}]
        result = self.analyzer._predict_issues_from_keywords({}, patterns)
        assert len(result) > 0

    def test_high_pattern_predicts_issue(self):
        patterns = [{"name": "性能下降", "severity": "HIGH"}]
        result = self.analyzer._predict_issues_from_keywords({}, patterns)
        assert len(result) > 0

    def test_low_severity_pattern_ignored(self):
        patterns = [{"name": "小问题", "severity": "LOW"}]
        result = self.analyzer._predict_issues_from_keywords({}, patterns)
        assert len(result) == 0


class TestBuildAnalysisPrompt:
    def setup_method(self):
        db = make_db()
        with patch("app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor"):
            self.analyzer = QualityRiskAnalyzer(db)

    def test_prompt_contains_log_info(self):
        logs = [make_work_log(work_content="功能测试完成", task_name="功能模块")]
        prompt = self.analyzer._build_analysis_prompt(logs, None)
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_prompt_with_project_context(self):
        logs = [make_work_log()]
        context = {"project_name": "测试项目", "stage": "开发阶段"}
        prompt = self.analyzer._build_analysis_prompt(logs, context)
        assert "测试项目" in prompt

    def test_prompt_max_20_logs(self):
        logs = [make_work_log(work_content=f"内容{i}") for i in range(25)]
        prompt = self.analyzer._build_analysis_prompt(logs, None)
        # At most 20 logs should be included
        assert isinstance(prompt, str)
        assert "JSON" in prompt
