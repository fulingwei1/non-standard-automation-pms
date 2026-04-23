# -*- coding: utf-8 -*-
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.schemas.presale_ai_knowledge import (
    AIQARequest,
    BestPracticeRequest,
    KnowledgeCaseCreate,
    KnowledgeCaseUpdate,
    KnowledgeExtractionRequest,
    SemanticSearchRequest,
)
from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService


def _make_case(**kwargs):
    base = dict(
        id=1,
        case_name="比亚迪ICT案例",
        industry="汽车",
        equipment_type="ICT",
        customer_name="比亚迪",
        project_amount=1500000,
        project_summary="ADAS ICT 测试方案",
        technical_highlights="自动化测试",
        success_factors="需求识别准确",
        lessons_learned="交付前需充分联调",
        tags=["汽车", "ICT"],
        quality_score=0.8,
        is_public=True,
        embedding=None,
        created_at=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


class TestPresaleAIKnowledgeServiceDeep2:
    @staticmethod
    def _make_service(db=None):
        db = db or MagicMock()
        with patch.object(PresaleAIKnowledgeService, "_get_embedding_model", return_value=None), patch(
            "app.services.presale.presale_ai_knowledge_service.AIClientService"
        ) as mock_ai_cls:
            ai_client = mock_ai_cls.return_value
            ai_client.default_model = "glm-4"
            ai_client.openai_client = None
            ai_client.openai_api_key = None
            ai_client.zhipu_client = None
            ai_client.kimi_api_key = None
            service = PresaleAIKnowledgeService(db)
        return service, db

    def test_semantic_search_applies_filters_and_ranks_results(self):
        service, db = self._make_service()

        top_case = _make_case(
            id=1,
            case_name="高匹配案例",
            embedding=service._serialize_embedding(np.array([1.0, 0.0], dtype=np.float32)),
        )
        fallback_case = _make_case(id=2, case_name="普通案例", embedding=None, tags=["ADAS"])

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [fallback_case, top_case]
        db.query.return_value = query_mock

        service._generate_embedding = MagicMock(return_value=np.array([1.0, 0.0], dtype=np.float32))
        service._keyword_similarity = MagicMock(return_value=0.35)

        req = SemanticSearchRequest(
            query="ADAS",
            industry="汽车",
            equipment_type="ICT",
            min_amount=100000,
            max_amount=2000000,
            top_k=1,
        )
        cases, total = service.semantic_search(req)

        assert total == 2
        assert [c.id for c in cases] == [1]
        assert cases[0].similarity_score == 1.0
        assert query_mock.filter.call_count >= 1

    def test_update_case_regenerates_embedding_and_refreshes_entity(self):
        service, db = self._make_service()
        case = _make_case(id=9, project_summary="旧摘要", embedding=None)

        db.query.return_value.filter.return_value.first.return_value = case
        service._generate_embedding = MagicMock(return_value=np.array([0.2, 0.4], dtype=np.float32))

        updated = service.update_case(9, KnowledgeCaseUpdate(project_summary="新摘要", tags=["新能源"]))

        assert updated is case
        assert case.project_summary == "新摘要"
        assert case.tags == ["新能源"]
        assert isinstance(case.embedding, bytes)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(case)

    def test_search_knowledge_base_uses_all_filters_and_pagination(self):
        service, db = self._make_service()

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 3
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            _make_case(id=3),
            _make_case(id=4),
        ]
        db.query.return_value = query_mock

        cases, total = service.search_knowledge_base(
            keyword="ADAS",
            tags=["汽车", "ICT"],
            industry="汽车",
            equipment_type="ICT",
            min_quality_score=0.7,
            page=2,
            page_size=2,
        )

        assert total == 3
        assert [c.id for c in cases] == [3, 4]
        query_mock.order_by.return_value.offset.assert_called_once_with(2)
        query_mock.order_by.return_value.offset.return_value.limit.assert_called_once_with(2)

    def test_extract_case_knowledge_auto_saves_high_confidence_result(self):
        service, _ = self._make_service()
        ai_extraction = {
            "case_name": "宁德时代装配线案例",
            "industry": "新能源",
            "equipment_type": "装配线",
            "customer_name": "宁德时代",
            "project_amount": 2600000,
            "project_summary": "高节拍装配线方案",
            "technical_highlights": "视觉定位+防错",
            "success_factors": "节拍平衡",
            "lessons_learned": "前期接口要锁定",
            "tags": ["新能源", "装配线"],
            "quality_score": 0.9,
        }
        service._extract_case_knowledge_with_ai = MagicMock(return_value=ai_extraction)
        service.create_case = MagicMock(return_value=_make_case(id=88, case_name="saved"))

        req = KnowledgeExtractionRequest(
            project_data={
                "project_name": "CATL Pack",
                "description": "新能源装配线",
                "industry": "新能源",
                "equipment_type": "装配线",
                "amount": 2600000,
            },
            auto_save=True,
        )
        result = service.extract_case_knowledge(req)

        assert result["extraction_confidence"] == 1.0
        assert result["extracted_case"].case_name == "宁德时代装配线案例"
        assert result["suggested_tags"] == ["新能源", "装配线"]
        assert "高质量案例" in result["quality_assessment"]
        service.create_case.assert_called_once()

    def test_ask_question_persists_qa_record_and_returns_sources(self):
        service, db = self._make_service()
        matched_cases = [_make_case(id=11, case_name="案例A"), _make_case(id=22, case_name="案例B")]
        service.semantic_search = MagicMock(return_value=(matched_cases, 2))
        service._generate_answer = MagicMock(return_value="先做ICT，再做老化")

        def add_side_effect(obj):
            obj.id = 66

        db.add.side_effect = add_side_effect

        result = service.ask_question(AIQARequest(question="怎么规划测试线？", context={"industry": "汽车"}), user_id=7)

        assert result["answer"] == "先做ICT，再做老化"
        assert result["confidence_score"] == 0.6
        assert result["sources"] == ["案例#11: 案例A", "案例#22: 案例B"]
        assert result["qa_id"] == 66
        db.commit.assert_called_once()

    def test_generate_ai_content_skips_mock_model_and_uses_fallback_model(self):
        service, _ = self._make_service()
        service.ai_model = "primary-model"
        service.ai_client.default_model = "fallback-model"
        service.ai_client.generate_solution.side_effect = [
            {"content": "mock content", "model": "primary-model-mock"},
            {"content": "正式答案", "model": "fallback-model"},
        ]
        service._has_live_ai = MagicMock(return_value=True)

        content = service._generate_ai_content("prompt")

        assert content == "正式答案"
        assert service.ai_client.generate_solution.call_count == 2

    def test_create_case_generates_embedding_and_saves(self):
        service, db = self._make_service()
        service._generate_embedding = MagicMock(return_value=np.array([0.6, 0.8], dtype=np.float32))

        with patch("app.services.presale.presale_ai_knowledge_service.save_obj") as mock_save:
            case = service.create_case(
                KnowledgeCaseCreate(
                    case_name="新案例",
                    industry="汽车",
                    equipment_type="ICT",
                    customer_name="客户A",
                    project_amount=1000,
                    project_summary="摘要",
                    technical_highlights="亮点",
                    success_factors="成功",
                    lessons_learned="教训",
                    tags=["汽车"],
                    quality_score=0.9,
                    is_public=True,
                )
            )

        assert case.case_name == "新案例"
        assert isinstance(case.embedding, bytes)
        mock_save.assert_called_once_with(db, case)

    def test_recommend_best_practices_prefers_high_quality_cases(self):
        service, _ = self._make_service()
        high = _make_case(id=1, quality_score=0.9)
        low = _make_case(id=2, quality_score=0.5)
        service.semantic_search = MagicMock(return_value=([high, low], 2))

        result = service.recommend_best_practices(
            BestPracticeRequest(scenario="新能源装配", industry="新能源", equipment_type="装配线", top_k=1)
        )

        assert [c.id for c in result["recommended_cases"]] == [1]
        assert "主要成功模式包括" in result["success_pattern_analysis"]
        assert result["risk_warnings"]

    def test_submit_qa_feedback_updates_score_and_handles_missing_record(self):
        service, db = self._make_service()
        qa = _make_case(id=5)
        db.query.return_value.filter.return_value.first.side_effect = [qa, None]

        assert service.submit_qa_feedback(5, 4, "有帮助") is True
        assert qa.feedback_score == 4
        assert service.submit_qa_feedback(999, 3) is False
        assert db.commit.call_count == 1

    def test_get_all_tags_collects_and_counts_distinct_values(self):
        service, db = self._make_service()
        db.query.return_value.all.return_value = [
            _make_case(tags=["汽车", "ICT"]),
            _make_case(tags=["ICT", "视觉"]),
        ]

        result = service.get_all_tags()

        assert result == {
            "tags": ["ICT", "汽车", "视觉"],
            "tag_counts": {"汽车": 1, "ICT": 2, "视觉": 1},
        }

    def test_generate_embedding_prefers_model_and_falls_back_to_hash_vector(self):
        service, _ = self._make_service()
        service.use_semantic_search = True
        service.embedding_model = MagicMock()
        service.embedding_model.encode.side_effect = RuntimeError("boom")

        vec = service._generate_embedding("ADAS 测试")
        empty = service._generate_embedding("")

        assert vec.shape == (384,)
        assert float(np.linalg.norm(vec)) == pytest.approx(1.0)
        assert empty.shape == (384,)
        assert float(empty.sum()) == 0.0

    def test_helper_methods_cover_text_tag_quality_and_warnings(self):
        service, _ = self._make_service()

        assert service._generate_summary({"project_name": "A", "description": "B", "objectives": "C"}) == "项目名称：A | 项目描述：B | 项目目标：C"
        assert service._generate_summary({}) == "项目摘要待补充"
        assert service._extract_highlights({"highlights": "亮点"}) == "亮点"
        assert service._extract_success_factors({"status": "completed", "success_rate": 0.9}) == "项目成功完成，达到预期目标"
        assert service._extract_lessons({}) == "暂无失败教训记录"
        assert service._suggest_tags({"industry": "汽车", "equipment_type": "ICT", "technology": "视觉", "amount": 2000000}) == ["汽车", "ICT", "视觉", "大型项目"]
        assert service._suggest_tags({}) == ["通用案例"]
        assert service._assess_quality({"description": "desc", "technical_highlights": "hi", "status": "completed"}) == 1.0
        assert service._calculate_extraction_confidence(
            {"project_name": "A", "description": "B", "industry": "C", "equipment_type": "D"},
            {"project_summary": "x", "technical_highlights": "y", "success_factors": "z", "lessons_learned": "k", "tags": ["t"]},
        ) == 1.0
        assert "高质量案例" in service._generate_quality_assessment(_make_case(), 0.8)
        assert service._generate_answer("问题", [], {}) == "抱歉，在知识库中未找到相关案例。建议您详细描述问题或联系技术专家。"
        assert "根据知识库中的1个相关案例分析" in service._generate_answer("问题", [_make_case(case_name="案例1", technical_highlights="亮点1")], {})
        assert service._normalize_text([" a ", "", "b"]) == "a\nb"
        assert service._normalize_text(None) is None
        assert service._normalize_tags("汽车, ICT，视觉;汽车") == ["汽车", "ICT", "视觉"]
        assert service._normalize_quality_score("1.5") == 1.0
        assert service._normalize_quality_score("bad") is None
        assert service._extract_risk_warnings([_make_case(lessons_learned="布线空间不足"), _make_case(lessons_learned="布线空间不足")]) == ["注意：布线空间不足"]
        assert service._extract_risk_warnings([_make_case(lessons_learned=""), _make_case(lessons_learned=None)]) == ["建议仔细评估技术可行性", "注意客户需求的准确理解"]
        assert "主要成功模式包括" in service._analyze_success_patterns([_make_case(success_factors="方案完整")])
        assert service._analyze_success_patterns([]) == "暂无足够案例进行分析"
        assert service._keyword_similarity(
            "adas",
            _make_case(case_name="ADAS案例", project_summary="ADAS方案", technical_highlights="ADAS亮点", tags=["ADAS"]),
        ) == pytest.approx(1.0)

    def test_delete_case_calls_delete_obj_and_handles_missing_case(self):
        service, db = self._make_service()
        case = _make_case(id=9)
        service.get_case = MagicMock(side_effect=[case, None])

        with patch("app.services.presale.presale_ai_knowledge_service.delete_obj") as mock_delete:
            assert service.delete_case(9) is True
            mock_delete.assert_called_once_with(db, case)

        assert service.delete_case(99) is False

    def test_recommend_best_practices_falls_back_when_no_high_quality_case(self):
        service, _ = self._make_service()
        low1 = _make_case(id=1, quality_score=0.6, success_factors=None)
        low2 = _make_case(id=2, quality_score=0.5, success_factors=None)
        service.semantic_search = MagicMock(return_value=([low1, low2], 2))

        result = service.recommend_best_practices(
            BestPracticeRequest(scenario="普通项目", industry="汽车", equipment_type="ICT", top_k=1)
        )

        assert [c.id for c in result["recommended_cases"]] == [1]
        assert result["success_pattern_analysis"] == "成功要素数据不足，建议补充案例详情"
        assert result["risk_warnings"] == ["注意：交付前需充分联调"]

    def test_generate_embedding_uses_working_model_output(self):
        service, _ = self._make_service()
        service.use_semantic_search = True
        service.embedding_model = MagicMock()
        service.embedding_model.encode.return_value = np.array([3.0, 4.0], dtype=np.float32)

        vec = service._generate_embedding("ADAS")

        assert vec.tolist() == pytest.approx([0.6, 0.8])
        assert vec.dtype == np.float32

    def test_generate_ai_content_returns_none_when_no_live_ai_or_all_attempts_fail(self):
        service, _ = self._make_service()
        service._has_live_ai = MagicMock(return_value=False)
        assert service._generate_ai_content("prompt") is None

        service._has_live_ai = MagicMock(return_value=True)
        service.ai_model = "primary-model"
        service.ai_client.default_model = "fallback-model"
        service.ai_client.generate_solution.side_effect = [RuntimeError("boom"), {"content": "", "model": "fallback-model"}]

        assert service._generate_ai_content("prompt") is None

    def test_extract_case_knowledge_with_ai_normalizes_payload_and_invalid_json(self):
        service, _ = self._make_service()
        service._generate_ai_content = MagicMock(side_effect=["not-json", "json"])

        with patch("app.services.presale.presale_ai_knowledge_service.extract_json_payload", side_effect=[[], {
            "case_name": "案例A",
            "industry": "汽车",
            "equipment_type": "ICT",
            "customer_name": "客户A",
            "project_amount": 123,
            "project_summary": [" 摘要1 ", "", "摘要2"],
            "technical_highlights": " 亮点 ",
            "success_factors": "成功",
            "lessons_learned": "教训",
            "tags": "汽车, ICT，视觉",
            "quality_score": "0.85",
        }]):
            assert service._extract_case_knowledge_with_ai({"project_name": "P1"}) is None
            result = service._extract_case_knowledge_with_ai({"project_name": "P2"})

        assert result == {
            "case_name": "案例A",
            "industry": "汽车",
            "equipment_type": "ICT",
            "customer_name": "客户A",
            "project_amount": 123,
            "project_summary": "摘要1\n摘要2",
            "technical_highlights": "亮点",
            "success_factors": "成功",
            "lessons_learned": "教训",
            "tags": ["汽车", "ICT", "视觉"],
            "quality_score": 0.85,
        }

    def test_generate_answer_prefers_ai_and_helper_branches_cover_remaining_paths(self):
        service, _ = self._make_service()
        service._generate_answer_with_ai = MagicMock(return_value="AI直接答案")

        assert service._generate_answer("问题", [_make_case(case_name="案例1")], {}) == "AI直接答案"
        assert service._calculate_qa_confidence([]) == 0.0
        assert service._extract_success_factors({"status": "doing", "success_rate": 0.1}) == "成功要素待项目完成后总结"
        assert service._generate_quality_assessment(_make_case(), 0.7) == "中等质量案例（置信度70%），建议补充详细信息后保存"
        assert service._generate_quality_assessment(_make_case(), 0.2) == "低质量案例（置信度20%），建议人工审核后再保存"
        assert service._normalize_text("  ") is None
        assert service._normalize_text(" x ") == "x"
        assert service._normalize_tags([" 汽车 ", "", "汽车", "ICT"]) == ["汽车", "ICT"]
        assert service._normalize_tags(None) == []
        assert service._normalize_quality_score("") is None
        assert service._analyze_success_patterns([_make_case(success_factors=None)]) == "成功要素数据不足，建议补充案例详情"

    def test_get_embedding_model_handles_disabled_success_cached_and_failure(self):
        cls = PresaleAIKnowledgeService

        cls._embedding_model = "cached"
        cls._embedding_model_checked = True
        assert cls._get_embedding_model() == "cached"

        cls._embedding_model = None
        cls._embedding_model_checked = False
        with patch("app.services.presale.presale_ai_knowledge_service.SEMANTIC_SEARCH_AVAILABLE", False):
            assert cls._get_embedding_model() is None
            assert cls._embedding_model_checked is True

        cls._embedding_model = None
        cls._embedding_model_checked = False
        fake_model = MagicMock(name="embedding_model")
        with patch("app.services.presale.presale_ai_knowledge_service.SEMANTIC_SEARCH_AVAILABLE", True), patch(
            "app.services.presale.presale_ai_knowledge_service.SentenceTransformer", return_value=fake_model
        ) as mock_transformer:
            assert cls._get_embedding_model() is fake_model
            assert cls._get_embedding_model() is fake_model
            mock_transformer.assert_called_once()

        cls._embedding_model = None
        cls._embedding_model_checked = False
        with patch("app.services.presale.presale_ai_knowledge_service.SEMANTIC_SEARCH_AVAILABLE", True), patch(
            "app.services.presale.presale_ai_knowledge_service.SentenceTransformer", side_effect=RuntimeError("boom")
        ):
            assert cls._get_embedding_model() is None

    def test_update_case_and_get_case_handle_missing_and_direct_fetch(self):
        service, db = self._make_service()
        first_query = MagicMock()
        first_query.filter.return_value.first.side_effect = [None, _make_case(id=12)]
        db.query.return_value = first_query

        assert service.update_case(404, KnowledgeCaseUpdate(tags=["x"])) is None
        assert service.get_case(12).id == 12

    def test_semantic_search_returns_empty_when_no_case_matches(self):
        service, db = self._make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        cases, total = service.semantic_search(SemanticSearchRequest(query="空", top_k=3))

        assert cases == []
        assert total == 0

    def test_cosine_similarity_returns_zero_when_vector_norm_is_zero(self):
        service, _ = self._make_service()
        assert service._cosine_similarity(np.zeros(2, dtype=np.float32), np.array([1.0, 0.0], dtype=np.float32)) == 0.0
