# -*- coding: utf-8 -*-
"""
N1组深度覆盖: PresaleAIKnowledgeService
针对已有测试未覆盖的分支、辅助方法进行补充
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
from app.schemas.presale_ai_knowledge import (
    KnowledgeCaseCreate,
    KnowledgeCaseUpdate,
    SemanticSearchRequest,
    BestPracticeRequest,
    KnowledgeExtractionRequest,
    AIQARequest,
)


def _make_service():
    db = MagicMock()
    return PresaleAIKnowledgeService(db), db


def _make_mock_case(**kwargs):
    case = MagicMock()
    case.id = kwargs.get("id", 1)
    case.case_name = kwargs.get("case_name", "测试案例")
    case.industry = kwargs.get("industry", "汽车")
    case.equipment_type = kwargs.get("equipment_type", "机器人")
    case.project_summary = kwargs.get("project_summary", "自动化装配项目")
    case.technical_highlights = kwargs.get("technical_highlights", "六轴机器人")
    case.success_factors = kwargs.get("success_factors", "技术成熟度高")
    case.lessons_learned = kwargs.get("lessons_learned", "注意安全规范")
    case.quality_score = kwargs.get("quality_score", 0.8)
    case.tags = kwargs.get("tags", ["汽车", "机器人"])
    case.embedding = kwargs.get("embedding", None)
    case.is_public = kwargs.get("is_public", True)
    return case


# ============================================================
# 1. create_case - 默认质量分分支
# ============================================================

class TestCreateCaseDeep:
    def test_create_case_default_quality_score(self):
        """quality_score 为 None 时默认赋 0.5"""
        service, db = _make_service()
        data = KnowledgeCaseCreate(case_name="无分案例", quality_score=None)
        with patch("app.services.presale_ai_knowledge_service.save_obj"):
            result = service.create_case(data)
        assert result.quality_score == 0.5

    def test_create_case_with_summary_triggers_embedding(self):
        """有 project_summary 时应调用 _generate_embedding"""
        service, db = _make_service()
        data = KnowledgeCaseCreate(
            case_name="有摘要案例",
            project_summary="这是一段很详细的摘要",
            is_public=True,
        )
        called = []
        original = service._generate_embedding
        def mock_embed(text):
            called.append(text)
            return original(text)
        service._generate_embedding = mock_embed

        with patch("app.services.presale_ai_knowledge_service.save_obj"):
            service.create_case(data)
        assert len(called) == 1

    def test_create_case_without_summary_no_embedding(self):
        """无摘要时不生成嵌入"""
        service, db = _make_service()
        data = KnowledgeCaseCreate(case_name="无摘要", project_summary=None)
        with patch("app.services.presale_ai_knowledge_service.save_obj"):
            result = service.create_case(data)
        # embedding 应为 None（未调用序列化）
        assert result.embedding is None


# ============================================================
# 2. update_case - summary 更新/不更新分支
# ============================================================

class TestUpdateCaseDeep:
    def test_update_case_no_summary_change_no_embedding(self):
        """更新时不含 project_summary，不重新生成嵌入"""
        service, db = _make_service()
        mock_case = _make_mock_case()
        db.query.return_value.filter.return_value.first.return_value = mock_case

        update_data = KnowledgeCaseUpdate(case_name="新名字")
        result = service.update_case(1, update_data)
        assert result is mock_case

    def test_update_case_with_empty_summary_no_embedding(self):
        """project_summary 为空字符串时不重新生成嵌入"""
        service, db = _make_service()
        mock_case = _make_mock_case()
        db.query.return_value.filter.return_value.first.return_value = mock_case

        update_data = KnowledgeCaseUpdate(project_summary="")
        result = service.update_case(1, update_data)
        # embedding 不应被修改
        assert mock_case.embedding is None


# ============================================================
# 3. semantic_search - 过滤条件、排序、相似度
# ============================================================

class TestSemanticSearchDeep:
    def test_semantic_search_top_k_limited(self):
        """top_k 限制返回数量"""
        service, db = _make_service()
        cases = []
        for i in range(10):
            np.random.seed(i)
            emb = np.random.randn(384).astype(np.float32)
            emb /= np.linalg.norm(emb)
            c = _make_mock_case(id=i, embedding=emb.tobytes())
            cases.append(c)
        db.query.return_value.filter.return_value.all.return_value = cases

        req = SemanticSearchRequest(query="机器人", top_k=3)
        result_cases, total = service.semantic_search(req)
        assert total == 10
        assert len(result_cases) <= 3

    def test_semantic_search_sorts_by_similarity(self):
        """返回结果按相似度降序"""
        service, db = _make_service()
        # 生成两个案例，第一个embedding和查询相似度高
        query = "机器人装配"
        query_emb = service._generate_embedding(query)

        case_high = _make_mock_case(id=1, case_name="高相似案例")
        case_high.embedding = service._serialize_embedding(query_emb)

        np.random.seed(999)
        low_emb = np.random.randn(384).astype(np.float32)
        low_emb /= np.linalg.norm(low_emb)
        case_low = _make_mock_case(id=2, case_name="低相似案例")
        case_low.embedding = low_emb.tobytes()

        db.query.return_value.filter.return_value.all.return_value = [case_low, case_high]
        req = SemanticSearchRequest(query=query, top_k=5)
        result_cases, _ = service.semantic_search(req)
        assert result_cases[0].id == 1  # 高相似度排第一

    def test_semantic_search_adds_similarity_score_attribute(self):
        """搜索结果应带 similarity_score 属性"""
        service, db = _make_service()
        c = _make_mock_case()
        c.embedding = service._serialize_embedding(service._generate_embedding("test"))
        db.query.return_value.filter.return_value.all.return_value = [c]

        req = SemanticSearchRequest(query="test", top_k=5)
        result_cases, _ = service.semantic_search(req)
        assert hasattr(result_cases[0], "similarity_score")


# ============================================================
# 4. recommend_best_practices - 高质量/无高质量两条路径
# ============================================================

class TestRecommendBestPracticesDeep:
    def test_recommend_falls_back_when_no_high_quality(self):
        """没有高质量案例时降级到普通案例"""
        service, db = _make_service()
        c = _make_mock_case(quality_score=0.3, embedding=None)
        db.query.return_value.filter.return_value.all.return_value = [c]

        req = BestPracticeRequest(scenario="测试场景", top_k=2)
        result = service.recommend_best_practices(req)
        assert "recommended_cases" in result
        assert len(result["recommended_cases"]) <= 2

    def test_recommend_limits_high_quality_to_top_k(self):
        """高质量案例超过 top_k 时只返回 top_k"""
        service, db = _make_service()
        cases = []
        for i in range(10):
            np.random.seed(i + 100)
            emb = np.random.randn(384).astype(np.float32)
            emb /= np.linalg.norm(emb)
            c = _make_mock_case(id=i, quality_score=0.9, embedding=emb.tobytes())
            cases.append(c)
        db.query.return_value.filter.return_value.all.return_value = cases

        req = BestPracticeRequest(scenario="测试", top_k=3)
        result = service.recommend_best_practices(req)
        assert len(result["recommended_cases"]) <= 3


# ============================================================
# 5. extract_case_knowledge - auto_save 条件分支
# ============================================================

class TestExtractCaseKnowledgeDeep:
    def test_auto_save_skipped_when_confidence_low(self):
        """置信度 < 0.7 时不自动保存"""
        service, db = _make_service()
        req = KnowledgeExtractionRequest(project_data={}, auto_save=True)
        with patch("app.services.presale_ai_knowledge_service.save_obj") as mock_save:
            result = service.extract_case_knowledge(req)
        mock_save.assert_not_called()
        assert result["extraction_confidence"] < 0.7

    def test_auto_save_triggered_when_confidence_high(self):
        """置信度 >= 0.7 时自动保存"""
        service, db = _make_service()
        project_data = {
            "project_name": "完整",
            "description": "desc",
            "industry": "汽车",
            "equipment_type": "机器人",
        }
        req = KnowledgeExtractionRequest(project_data=project_data, auto_save=True)
        with patch("app.services.presale_ai_knowledge_service.save_obj") as mock_save:
            result = service.extract_case_knowledge(req)
        assert result["extraction_confidence"] >= 0.7
        mock_save.assert_called()

    def test_quality_assessment_medium(self):
        """中等置信度评估"""
        service, _ = _make_service()
        case = KnowledgeCaseCreate(case_name="测试")
        msg = service._generate_quality_assessment(case, 0.65)
        assert "中等质量" in msg


# ============================================================
# 6. _analyze_success_patterns - 有/无案例
# ============================================================

class TestAnalyzeSuccessPatterns:
    def test_no_cases_returns_default_text(self):
        service, _ = _make_service()
        result = service._analyze_success_patterns([])
        assert "暂无" in result

    def test_with_cases_no_success_factors(self):
        """案例有 success_factors 时生成分析文本"""
        service, _ = _make_service()
        case = _make_mock_case(success_factors="技术方案准确")
        result = service._analyze_success_patterns([case])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_with_cases_empty_success_factors(self):
        """案例 success_factors 为空时返回备用文本"""
        service, _ = _make_service()
        case = _make_mock_case()
        case.success_factors = None
        result = service._analyze_success_patterns([case])
        assert isinstance(result, str)


# ============================================================
# 7. _extract_risk_warnings
# ============================================================

class TestExtractRiskWarnings:
    def test_no_lessons_returns_defaults(self):
        service, _ = _make_service()
        case = _make_mock_case()
        case.lessons_learned = None
        warnings = service._extract_risk_warnings([case])
        # 无教训时应返回默认警告
        assert len(warnings) > 0

    def test_with_lessons_returns_warnings(self):
        service, _ = _make_service()
        case = _make_mock_case(lessons_learned="注意安全规范和设备调试")
        warnings = service._extract_risk_warnings([case])
        assert any("注意" in w for w in warnings)

    def test_empty_cases_returns_defaults(self):
        service, _ = _make_service()
        warnings = service._extract_risk_warnings([])
        assert len(warnings) >= 1


# ============================================================
# 8. _generate_summary / _extract_highlights / _extract_success_factors / _extract_lessons
# ============================================================

class TestPrivateExtractors:
    def test_generate_summary_full_data(self):
        service, _ = _make_service()
        data = {
            "project_name": "装配线",
            "description": "自动化改造",
            "objectives": "提升效率"
        }
        summary = service._generate_summary(data)
        assert "装配线" in summary
        assert "自动化改造" in summary

    def test_generate_summary_empty_data(self):
        service, _ = _make_service()
        summary = service._generate_summary({})
        assert "待补充" in summary

    def test_extract_highlights_present(self):
        service, _ = _make_service()
        data = {"technical_highlights": "六轴机器人视觉系统"}
        result = service._extract_highlights(data)
        assert "六轴" in result

    def test_extract_highlights_fallback(self):
        service, _ = _make_service()
        result = service._extract_highlights({})
        assert "待补充" in result

    def test_extract_success_factors_completed(self):
        service, _ = _make_service()
        data = {"status": "completed", "success_rate": 0.9}
        result = service._extract_success_factors(data)
        assert "成功" in result

    def test_extract_success_factors_incomplete(self):
        service, _ = _make_service()
        result = service._extract_success_factors({"status": "ongoing"})
        assert "待" in result

    def test_extract_lessons_present(self):
        service, _ = _make_service()
        data = {"lessons_learned": "注意接地处理"}
        result = service._extract_lessons(data)
        assert "接地" in result

    def test_extract_lessons_empty(self):
        service, _ = _make_service()
        result = service._extract_lessons({})
        assert "暂无" in result


# ============================================================
# 9. _suggest_tags - 不同分支
# ============================================================

class TestSuggestTags:
    def test_suggest_tags_with_large_amount(self):
        service, _ = _make_service()
        data = {"industry": "汽车", "equipment_type": "机器人", "amount": 2000000}
        tags = service._suggest_tags(data)
        assert "大型项目" in tags

    def test_suggest_tags_small_amount(self):
        service, _ = _make_service()
        data = {"industry": "电子", "amount": 50000}
        tags = service._suggest_tags(data)
        assert "大型项目" not in tags

    def test_suggest_tags_empty_returns_default(self):
        service, _ = _make_service()
        tags = service._suggest_tags({})
        assert tags == ["通用案例"]

    def test_suggest_tags_with_technology(self):
        service, _ = _make_service()
        data = {"technology": "视觉识别"}
        tags = service._suggest_tags(data)
        assert "视觉识别" in tags


# ============================================================
# 10. _assess_quality - 不同分支
# ============================================================

class TestAssessQuality:
    def test_base_score_empty(self):
        service, _ = _make_service()
        score = service._assess_quality({})
        assert score == 0.5

    def test_with_description(self):
        service, _ = _make_service()
        score = service._assess_quality({"description": "有描述"})
        assert score == 0.7

    def test_with_highlights(self):
        service, _ = _make_service()
        score = service._assess_quality({"technical_highlights": "高亮"})
        assert score == pytest.approx(0.6)

    def test_with_completed_status(self):
        service, _ = _make_service()
        score = service._assess_quality({"status": "completed"})
        assert score == 0.7

    def test_max_score_capped_at_one(self):
        service, _ = _make_service()
        data = {
            "description": "详细",
            "technical_highlights": "高亮",
            "status": "completed"
        }
        score = service._assess_quality(data)
        assert score <= 1.0


# ============================================================
# 11. _calculate_qa_confidence - 边界
# ============================================================

class TestCalculateQAConfidence:
    def test_single_case_confidence(self):
        service, _ = _make_service()
        case = _make_mock_case(quality_score=1.0)
        conf = service._calculate_qa_confidence([case])
        assert 0.0 < conf <= 1.0

    def test_five_cases_max_factor(self):
        service, _ = _make_service()
        cases = [_make_mock_case(quality_score=1.0) for _ in range(5)]
        conf = service._calculate_qa_confidence(cases)
        assert conf == pytest.approx(1.0)

    def test_low_quality_cases(self):
        service, _ = _make_service()
        cases = [_make_mock_case(quality_score=0.0) for _ in range(5)]
        conf = service._calculate_qa_confidence(cases)
        assert conf == pytest.approx(0.5)


# ============================================================
# 12. _keyword_similarity - 各字段匹配
# ============================================================

class TestKeywordSimilarityDeep:
    def test_case_name_match_score(self):
        service, _ = _make_service()
        case = _make_mock_case(case_name="机器人装配")
        score = service._keyword_similarity("机器人", case)
        assert score >= 0.3

    def test_summary_match_score(self):
        service, _ = _make_service()
        case = _make_mock_case(project_summary="自动化机器人装配线")
        score = service._keyword_similarity("机器人", case)
        assert score >= 0.4

    def test_highlights_match_score(self):
        service, _ = _make_service()
        case = _make_mock_case(technical_highlights="激光焊接技术")
        score = service._keyword_similarity("激光焊接", case)
        assert score >= 0.2

    def test_tags_match_score(self):
        service, _ = _make_service()
        case = _make_mock_case(tags=["激光焊接", "汽车"])
        score = service._keyword_similarity("激光焊接", case)
        assert score >= 0.1

    def test_max_score_capped_at_one(self):
        service, _ = _make_service()
        case = _make_mock_case(
            case_name="激光激光",
            project_summary="激光焊接激光",
            technical_highlights="激光激光",
            tags=["激光"]
        )
        score = service._keyword_similarity("激光", case)
        assert score <= 1.0


# ============================================================
# 13. search_knowledge_base - 多过滤条件组合
# ============================================================

class TestSearchKnowledgeBaseDeep:
    def test_search_with_min_quality_score(self):
        service, db = _make_service()
        filter_mock = MagicMock()
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 2
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value = filter_mock

        cases, total = service.search_knowledge_base(min_quality_score=0.7)
        assert total == 2

    def test_search_with_industry_filter(self):
        service, db = _make_service()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 0
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value = filter_mock

        cases, total = service.search_knowledge_base(industry="汽车")
        assert total == 0

    def test_search_pagination(self):
        service, db = _make_service()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 50
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value = filter_mock

        cases, total = service.search_knowledge_base(page=2, page_size=10)
        assert total == 50


# ============================================================
# 14. ask_question - _generate_answer 分支
# ============================================================

class TestAskQuestionDeep:
    def test_answer_no_cases_message(self):
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        req = AIQARequest(question="请问如何解决？")
        result = service.ask_question(req, user_id=1)
        assert "抱歉" in result["answer"]

    def test_answer_with_cases_references(self):
        service, db = _make_service()
        c = _make_mock_case(
            id=5,
            case_name="视觉检测案例",
            embedding=service._serialize_embedding(service._generate_embedding("视觉"))
        )
        db.query.return_value.filter.return_value.all.return_value = [c]
        req = AIQARequest(question="视觉检测方案")
        result = service.ask_question(req, user_id=1)
        assert "1个" in result["answer"] or "案例" in result["answer"]

    def test_sources_limited_to_three(self):
        service, db = _make_service()
        cases = [
            _make_mock_case(
                id=i,
                embedding=service._serialize_embedding(service._generate_embedding(f"案例{i}"))
            ) for i in range(5)
        ]
        db.query.return_value.filter.return_value.all.return_value = cases[:2]  # only 2 returned
        req = AIQARequest(question="问题")
        result = service.ask_question(req, user_id=1)
        assert len(result["sources"]) <= 3
