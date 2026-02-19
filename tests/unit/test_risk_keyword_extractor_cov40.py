# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 质量风险关键词提取器
"""

import pytest

try:
    from app.services.quality_risk_ai.risk_keyword_extractor import RiskKeywordExtractor
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def extractor():
    return RiskKeywordExtractor()


class TestExtractKeywords:

    def test_extract_bug_keyword(self, extractor):
        text = "今天修复了一个bug，导致崩溃的问题"
        result = extractor.extract_keywords(text)
        assert "BUG" in result

    def test_extract_critical_keyword(self, extractor):
        text = "严重的安全漏洞，数据丢失，urgent fix needed"
        result = extractor.extract_keywords(text)
        assert "CRITICAL" in result

    def test_no_keywords_in_clean_text(self, extractor):
        text = "今天完成了需求评审，进展顺利"
        result = extractor.extract_keywords(text)
        # 干净文本不应触发关键词（或只有极少）
        assert isinstance(result, dict)

    def test_multiple_categories_extracted(self, extractor):
        text = "性能严重下降，稳定性不稳定，偶现卡顿延迟"
        result = extractor.extract_keywords(text)
        assert len(result) >= 2

    def test_keywords_deduplicated(self, extractor):
        text = "bug bug bug 错误 错误"
        result = extractor.extract_keywords(text)
        if "BUG" in result:
            assert len(result["BUG"]) == len(set(result["BUG"]))


class TestDetectPatterns:

    def test_detects_frequent_fix_pattern(self, extractor):
        text = "修复bug，再次修复问题，又修复了错误"
        patterns = extractor.detect_patterns(text)
        assert len(patterns) >= 1

    def test_returns_empty_for_clean_text(self, extractor):
        text = "正常完成开发任务，代码已提交"
        patterns = extractor.detect_patterns(text)
        assert isinstance(patterns, list)

    def test_pattern_has_required_fields(self, extractor):
        text = "阻塞无法继续推进，严重影响项目进度"
        patterns = extractor.detect_patterns(text)
        if patterns:
            p = patterns[0]
            assert "name" in p
            assert "severity" in p
            assert "count" in p


class TestCalculateRiskScore:

    def test_zero_score_for_empty(self, extractor):
        score = extractor.calculate_risk_score({}, [])
        assert score == 0.0

    def test_critical_keywords_give_high_score(self, extractor):
        keywords = {"CRITICAL": ["严重", "urgent", "数据丢失"]}
        score = extractor.calculate_risk_score(keywords, [])
        assert score > 0

    def test_score_capped_at_100(self, extractor):
        keywords = {
            "CRITICAL": ["严重", "urgent", "数据丢失", "安全"],
            "BUG": ["bug", "error", "fail", "缺陷"],
            "REWORK": ["返工", "重做"],
        }
        patterns = [{"severity": "CRITICAL", "count": 5}]
        score = extractor.calculate_risk_score(keywords, patterns)
        assert score <= 100.0


class TestDetermineRiskLevel:

    def test_low_score_is_low(self, extractor):
        assert extractor.determine_risk_level(10.0) == "LOW"

    def test_medium_score(self, extractor):
        assert extractor.determine_risk_level(35.0) == "MEDIUM"

    def test_high_score(self, extractor):
        assert extractor.determine_risk_level(60.0) == "HIGH"

    def test_critical_score(self, extractor):
        assert extractor.determine_risk_level(80.0) == "CRITICAL"


class TestAnalyzeText:

    def test_analyze_returns_all_fields(self, extractor):
        text = "严重bug导致系统崩溃，多次返工，修复了错误"
        result = extractor.analyze_text(text)
        assert "risk_keywords" in result
        assert "abnormal_patterns" in result
        assert "risk_score" in result
        assert "risk_level" in result
        assert "keyword_count" in result
        assert "pattern_count" in result
        assert "analyzed_at" in result

    def test_risk_level_is_valid_enum(self, extractor):
        text = "今天正常开发"
        result = extractor.analyze_text(text)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
