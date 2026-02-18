# -*- coding: utf-8 -*-
"""第二十八批 - quality_risk_analyzer 单元测试（质量风险AI分析器）"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.quality_risk_ai.quality_risk_analyzer")

from app.services.quality_risk_ai.quality_risk_analyzer import QualityRiskAnalyzer


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_log(
    work_date="2024-01-01",
    user_name="张三",
    task_name="模块A",
    work_content="完成功能开发",
    work_result="通过测试",
):
    return {
        "work_date": work_date,
        "user_name": user_name,
        "task_name": task_name,
        "work_content": work_content,
        "work_result": work_result,
    }


def _make_analyzer(db=None):
    if db is None:
        db = MagicMock()
    with patch(
        "app.services.quality_risk_ai.quality_risk_analyzer.RiskKeywordExtractor"
    ) as mock_cls:
        extractor = MagicMock()
        mock_cls.return_value = extractor
        analyzer = QualityRiskAnalyzer(db)
        analyzer.keyword_extractor = extractor
    return analyzer


# ─── analyze_work_logs ───────────────────────────────────────

class TestAnalyzeWorkLogs:

    def test_returns_low_risk_for_empty_logs(self):
        analyzer = _make_analyzer()
        result = analyzer.analyze_work_logs(work_logs=[])
        assert result["risk_level"] == "LOW"
        assert result["risk_score"] == 0.0
        assert result["risk_signals"] == []

    def test_calls_keyword_extractor_for_each_log(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.return_value = {
            "risk_keywords": {},
            "abnormal_patterns": [],
            "risk_score": 10.0,
        }
        analyzer.keyword_extractor.determine_risk_level.return_value = "LOW"
        analyzer.keyword_extractor._predict_issues_from_keywords = MagicMock(return_value=[])

        logs = [_make_log(), _make_log(user_name="李四")]
        analyzer.analyze_work_logs(logs)

        assert analyzer.keyword_extractor.analyze_text.call_count == 2

    def test_returns_keyword_analysis_when_score_low(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.return_value = {
            "risk_keywords": {"delay": ["延迟"]},
            "abnormal_patterns": [],
            "risk_score": 20.0,
        }
        analyzer.keyword_extractor.determine_risk_level.return_value = "MEDIUM"

        with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
            logs = [_make_log()]
            result = analyzer.analyze_work_logs(logs)

        assert result["risk_level"] == "MEDIUM"
        assert result["ai_confidence"] == 60.0

    @patch("app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY", "fake-key")
    def test_falls_back_to_keyword_when_glm_fails(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.return_value = {
            "risk_keywords": {},
            "abnormal_patterns": [],
            "risk_score": 50.0,  # 触发 AI 分析
        }
        analyzer.keyword_extractor.determine_risk_level.return_value = "HIGH"

        with patch.object(analyzer, "_analyze_with_glm", side_effect=Exception("API Error")):
            with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
                logs = [_make_log()]
                result = analyzer.analyze_work_logs(logs)

        # 降级到关键词分析
        assert result["risk_level"] == "HIGH"


# ─── _analyze_with_keywords ──────────────────────────────────

class TestAnalyzeWithKeywords:

    def test_aggregates_keywords_from_all_logs(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.side_effect = [
            {"risk_keywords": {"delay": ["超期"]}, "abnormal_patterns": [], "risk_score": 15.0},
            {"risk_keywords": {"delay": ["延误"]}, "abnormal_patterns": [], "risk_score": 10.0},
        ]
        analyzer.keyword_extractor.determine_risk_level.return_value = "LOW"

        with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
            result = analyzer._analyze_with_keywords([_make_log(), _make_log()])

        delay_keywords = result["risk_keywords"].get("delay", [])
        assert len(delay_keywords) == 2

    def test_deduplicates_keywords(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.side_effect = [
            {"risk_keywords": {"quality": ["缺陷"]}, "abnormal_patterns": [], "risk_score": 20.0},
            {"risk_keywords": {"quality": ["缺陷"]}, "abnormal_patterns": [], "risk_score": 20.0},
        ]
        analyzer.keyword_extractor.determine_risk_level.return_value = "MEDIUM"

        with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
            result = analyzer._analyze_with_keywords([_make_log(), _make_log()])

        quality_keywords = result["risk_keywords"].get("quality", [])
        # 去重后只有 1 个
        assert len(quality_keywords) == 1

    def test_risk_signals_recorded_when_score_gt_20(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.return_value = {
            "risk_keywords": {"danger": ["严重"]},
            "abnormal_patterns": [],
            "risk_score": 35.0,
        }
        analyzer.keyword_extractor.determine_risk_level.return_value = "HIGH"

        with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
            result = analyzer._analyze_with_keywords([_make_log()])

        assert len(result["risk_signals"]) == 1
        assert result["risk_signals"][0]["risk_score"] == 35.0

    def test_no_risk_signals_when_score_le_20(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.return_value = {
            "risk_keywords": {},
            "abnormal_patterns": [],
            "risk_score": 15.0,
        }
        analyzer.keyword_extractor.determine_risk_level.return_value = "LOW"

        with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
            result = analyzer._analyze_with_keywords([_make_log()])

        assert result["risk_signals"] == []

    def test_average_score_computed_correctly(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.side_effect = [
            {"risk_keywords": {}, "abnormal_patterns": [], "risk_score": 20.0},
            {"risk_keywords": {}, "abnormal_patterns": [], "risk_score": 40.0},
        ]
        analyzer.keyword_extractor.determine_risk_level.return_value = "MEDIUM"

        with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
            result = analyzer._analyze_with_keywords([_make_log(), _make_log()])

        assert result["risk_score"] == pytest.approx(30.0, abs=0.01)

    def test_analysis_model_is_keyword_extractor(self):
        analyzer = _make_analyzer()
        analyzer.keyword_extractor.analyze_text.return_value = {
            "risk_keywords": {},
            "abnormal_patterns": [],
            "risk_score": 0.0,
        }
        analyzer.keyword_extractor.determine_risk_level.return_value = "LOW"

        with patch.object(analyzer, "_predict_issues_from_keywords", return_value=[]):
            result = analyzer._analyze_with_keywords([_make_log()])

        assert result["analysis_model"] == "KEYWORD_EXTRACTOR"
        assert result["ai_analysis"]["method"] == "KEYWORD_BASED"
        assert result["ai_analysis"]["logs_analyzed"] == 1
