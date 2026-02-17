# -*- coding: utf-8 -*-
"""
I1组: PresaleAIKnowledgeService 单元测试
直接实例化类，用 MagicMock 替代 db session
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, call

from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
from app.schemas.presale_ai_knowledge import (
    KnowledgeCaseCreate,
    KnowledgeCaseUpdate,
    SemanticSearchRequest,
    BestPracticeRequest,
    KnowledgeExtractionRequest,
    AIQARequest,
)


# ============================================================
# Helper factory
# ============================================================

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
# TestCreateCase
# ============================================================

class TestCreateCase:
    def test_create_case_basic(self):
        """创建基本案例"""
        service, db = _make_service()
        data = KnowledgeCaseCreate(
            case_name="新案例",
            industry="汽车",
            project_summary="测试摘要",
        )

        with patch("app.services.presale_ai_knowledge_service.save_obj") as mock_save:
            result = service.create_case(data)

        mock_save.assert_called_once()
        assert result is not None

    def test_create_case_without_summary(self):
        """创建无摘要的案例，不生成嵌入"""
        service, db = _make_service()
        data = KnowledgeCaseCreate(case_name="无摘要案例")

        with patch("app.services.presale_ai_knowledge_service.save_obj") as mock_save:
            result = service.create_case(data)

        mock_save.assert_called_once()

    def test_create_case_with_quality_score(self):
        """创建带质量分的案例"""
        service, db = _make_service()
        data = KnowledgeCaseCreate(
            case_name="高质量案例",
            project_summary="详细摘要",
            quality_score=0.9,
        )

        with patch("app.services.presale_ai_knowledge_service.save_obj"):
            result = service.create_case(data)
        assert result.quality_score == 0.9


# ============================================================
# TestUpdateCase
# ============================================================

class TestUpdateCase:
    def test_update_case_found(self):
        """更新存在的案例"""
        service, db = _make_service()
        mock_case = _make_mock_case()
        db.query.return_value.filter.return_value.first.return_value = mock_case

        update_data = KnowledgeCaseUpdate(case_name="更新名称")
        result = service.update_case(1, update_data)

        assert result is mock_case
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(mock_case)

    def test_update_case_not_found(self):
        """更新不存在的案例返回 None"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        update_data = KnowledgeCaseUpdate(case_name="更新")
        result = service.update_case(999, update_data)
        assert result is None

    def test_update_case_regenerates_embedding_when_summary_updated(self):
        """更新摘要时重新生成嵌入"""
        service, db = _make_service()
        mock_case = _make_mock_case()
        db.query.return_value.filter.return_value.first.return_value = mock_case

        update_data = KnowledgeCaseUpdate(project_summary="新摘要")
        result = service.update_case(1, update_data)

        # 验证 embedding 被设置
        assert mock_case.embedding is not None


# ============================================================
# TestGetCase
# ============================================================

class TestGetCase:
    def test_get_case_found(self):
        """获取存在的案例"""
        service, db = _make_service()
        mock_case = _make_mock_case()
        db.query.return_value.filter.return_value.first.return_value = mock_case

        result = service.get_case(1)
        assert result is mock_case

    def test_get_case_not_found(self):
        """获取不存在的案例"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_case(999)
        assert result is None


# ============================================================
# TestDeleteCase
# ============================================================

class TestDeleteCase:
    def test_delete_case_success(self):
        """删除存在的案例"""
        service, db = _make_service()
        mock_case = _make_mock_case()
        db.query.return_value.filter.return_value.first.return_value = mock_case

        with patch("app.services.presale_ai_knowledge_service.delete_obj") as mock_del:
            result = service.delete_case(1)

        assert result is True
        mock_del.assert_called_once_with(db, mock_case)

    def test_delete_case_not_found(self):
        """删除不存在的案例返回 False"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.delete_case(999)
        assert result is False


# ============================================================
# TestSemanticSearch
# ============================================================

class TestSemanticSearch:
    def test_semantic_search_no_cases(self):
        """没有案例时返回空列表"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        req = SemanticSearchRequest(query="机器人装配")
        cases, total = service.semantic_search(req)

        assert cases == []
        assert total == 0

    def test_semantic_search_with_embedding(self):
        """有嵌入向量时进行余弦相似度计算"""
        service, db = _make_service()

        # 生成真实嵌入
        np.random.seed(42)
        emb = np.random.randn(384).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        blob = emb.tobytes()

        mock_case = _make_mock_case(embedding=blob, quality_score=0.8)
        db.query.return_value.filter.return_value.all.return_value = [mock_case]

        req = SemanticSearchRequest(query="汽车装配", top_k=5)
        cases, total = service.semantic_search(req)

        assert total == 1
        assert len(cases) <= 1

    def test_semantic_search_with_filters(self):
        """带行业和设备类型过滤"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        req = SemanticSearchRequest(
            query="自动化",
            industry="汽车",
            equipment_type="机器人",
            min_amount=100000,
            max_amount=1000000,
        )
        cases, total = service.semantic_search(req)
        assert cases == []
        assert total == 0

    def test_semantic_search_no_embedding_fallback(self):
        """无嵌入时使用关键词相似度"""
        service, db = _make_service()
        mock_case = _make_mock_case(embedding=None, case_name="自动化项目")
        db.query.return_value.filter.return_value.all.return_value = [mock_case]

        req = SemanticSearchRequest(query="自动化", top_k=5)
        cases, total = service.semantic_search(req)
        assert total == 1


# ============================================================
# TestRecommendBestPractices
# ============================================================

class TestRecommendBestPractices:
    def test_recommend_best_practices_no_cases(self):
        """没有案例时也能返回结构"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        req = BestPracticeRequest(scenario="汽车装配线改造")
        result = service.recommend_best_practices(req)

        assert "recommended_cases" in result
        assert "success_pattern_analysis" in result
        assert "risk_warnings" in result

    def test_recommend_best_practices_with_high_quality_cases(self):
        """高质量案例推荐"""
        service, db = _make_service()
        # 构造高质量案例的嵌入
        np.random.seed(10)
        emb = np.random.randn(384).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        blob = emb.tobytes()

        mock_case = _make_mock_case(embedding=blob, quality_score=0.9)
        db.query.return_value.filter.return_value.all.return_value = [mock_case]

        req = BestPracticeRequest(scenario="机器人装配", top_k=3)
        result = service.recommend_best_practices(req)

        assert "recommended_cases" in result


# ============================================================
# TestExtractCaseKnowledge
# ============================================================

class TestExtractCaseKnowledge:
    def test_extract_case_knowledge_basic(self):
        """基本知识提取"""
        service, db = _make_service()
        project_data = {
            "project_name": "测试项目",
            "description": "自动化改造",
            "industry": "汽车",
            "equipment_type": "机器人",
        }
        req = KnowledgeExtractionRequest(project_data=project_data, auto_save=False)
        result = service.extract_case_knowledge(req)

        assert "extracted_case" in result
        assert "extraction_confidence" in result
        assert "suggested_tags" in result
        assert "quality_assessment" in result

    def test_extract_case_knowledge_auto_save(self):
        """高置信度时自动保存"""
        service, db = _make_service()
        project_data = {
            "project_name": "完整项目",
            "description": "非常详细的描述",
            "industry": "汽车",
            "equipment_type": "机器人",
            "technical_highlights": "先进视觉系统",
            "status": "completed",
        }
        req = KnowledgeExtractionRequest(project_data=project_data, auto_save=True)

        with patch("app.services.presale_ai_knowledge_service.save_obj"):
            result = service.extract_case_knowledge(req)

        assert result["extraction_confidence"] >= 0.3

    def test_extract_case_knowledge_empty_project(self):
        """空项目数据提取"""
        service, db = _make_service()
        req = KnowledgeExtractionRequest(project_data={}, auto_save=False)
        result = service.extract_case_knowledge(req)

        assert result["extraction_confidence"] == 0.3


# ============================================================
# TestAskQuestion
# ============================================================

class TestAskQuestion:
    def test_ask_question_no_cases(self):
        """无案例时的问答"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        mock_qa = MagicMock()
        mock_qa.id = 42
        db.add.return_value = None

        req = AIQARequest(question="如何设计装配线?")
        result = service.ask_question(req, user_id=1)

        assert "answer" in result
        assert "confidence_score" in result
        db.add.assert_called()
        db.commit.assert_called()

    def test_ask_question_with_cases(self):
        """有案例时生成答案"""
        service, db = _make_service()
        np.random.seed(5)
        emb = np.random.randn(384).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        blob = emb.tobytes()

        mock_case = _make_mock_case(embedding=blob)
        db.query.return_value.filter.return_value.all.return_value = [mock_case]

        req = AIQARequest(question="机器人装配如何提高效率?")
        result = service.ask_question(req, user_id=1)

        assert "answer" in result
        assert "sources" in result

    def test_ask_question_with_context(self):
        """带上下文的问答"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        req = AIQARequest(question="需要哪些传感器?", context={"project_type": "装配"})
        result = service.ask_question(req, user_id=2)
        assert result is not None


# ============================================================
# TestSubmitQAFeedback
# ============================================================

class TestSubmitQAFeedback:
    def test_submit_feedback_success(self):
        """提交反馈成功"""
        service, db = _make_service()
        mock_qa = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_qa

        result = service.submit_qa_feedback(qa_id=1, feedback_score=5)

        assert result is True
        assert mock_qa.feedback_score == 5
        db.commit.assert_called_once()

    def test_submit_feedback_not_found(self):
        """问答记录不存在"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = service.submit_qa_feedback(qa_id=999, feedback_score=3)
        assert result is False


# ============================================================
# TestSearchKnowledgeBase
# ============================================================

class TestSearchKnowledgeBase:
    def test_search_with_keyword(self):
        """关键词搜索"""
        service, db = _make_service()
        mock_cases = [_make_mock_case()]

        # count() 和 all() 各自 mock
        filter_mock = MagicMock()
        filter_mock.count.return_value = 1
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_cases
        db.query.return_value.filter.return_value = filter_mock

        cases, total = service.search_knowledge_base(keyword="机器人")
        assert total == 1

    def test_search_no_filters(self):
        """无过滤条件搜索"""
        service, db = _make_service()
        filter_mock = MagicMock()
        filter_mock.count.return_value = 0
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        db.query.return_value = filter_mock

        cases, total = service.search_knowledge_base()
        assert total == 0

    def test_search_with_tags(self):
        """带标签搜索"""
        service, db = _make_service()
        filter_mock = MagicMock()
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 2
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value = filter_mock

        cases, total = service.search_knowledge_base(tags=["汽车", "机器人"])
        assert total == 2


# ============================================================
# TestGetAllTags
# ============================================================

class TestGetAllTags:
    def test_get_all_tags_empty(self):
        """没有案例时返回空标签"""
        service, db = _make_service()
        db.query.return_value.all.return_value = []

        result = service.get_all_tags()
        assert result["tags"] == []
        assert result["tag_counts"] == {}

    def test_get_all_tags_with_cases(self):
        """有案例时正确统计标签"""
        service, db = _make_service()
        mock_case1 = _make_mock_case(tags=["汽车", "机器人"])
        mock_case2 = _make_mock_case(tags=["汽车", "视觉"])
        db.query.return_value.all.return_value = [mock_case1, mock_case2]

        result = service.get_all_tags()
        assert "汽车" in result["tags"]
        assert result["tag_counts"]["汽车"] == 2

    def test_get_all_tags_with_none_tags(self):
        """tags 为 None 的案例不影响结果"""
        service, db = _make_service()
        mock_case = _make_mock_case(tags=None)
        db.query.return_value.all.return_value = [mock_case]

        result = service.get_all_tags()
        assert result["tags"] == []


# ============================================================
# TestInternalHelpers
# ============================================================

class TestInternalHelpers:
    def test_generate_embedding_returns_normalized_vector(self):
        """生成的嵌入向量是归一化的"""
        service, _ = _make_service()
        emb = service._generate_embedding("测试文本")
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 1e-5

    def test_serialize_deserialize_embedding(self):
        """序列化和反序列化嵌入保持一致"""
        service, _ = _make_service()
        original = service._generate_embedding("测试")
        blob = service._serialize_embedding(original)
        restored = service._deserialize_embedding(blob)
        np.testing.assert_array_almost_equal(original, restored, decimal=5)

    def test_cosine_similarity_identical(self):
        """相同向量余弦相似度为1"""
        service, _ = _make_service()
        v = np.array([1.0, 0.0, 0.0])
        assert abs(service._cosine_similarity(v, v) - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        """正交向量余弦相似度为0"""
        service, _ = _make_service()
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        assert abs(service._cosine_similarity(v1, v2)) < 1e-6

    def test_keyword_similarity_match(self):
        """关键词在摘要中出现时分数增加"""
        service, _ = _make_service()
        mock_case = _make_mock_case(
            case_name="机器人装配项目",
            project_summary="机器人自动装配生产线",
        )
        score = service._keyword_similarity("机器人", mock_case)
        assert score > 0.0

    def test_keyword_similarity_no_match(self):
        """关键词不匹配时分数为0"""
        service, _ = _make_service()
        mock_case = _make_mock_case(
            case_name="包装线项目",
            project_summary="自动包装系统",
            technical_highlights="气动控制",
            tags=["包装"],
        )
        score = service._keyword_similarity("激光焊接", mock_case)
        assert score == 0.0

    def test_calculate_extraction_confidence_full_data(self):
        """完整数据置信度高"""
        service, _ = _make_service()
        project_data = {
            "project_name": "完整项目",
            "description": "详细描述",
            "industry": "汽车",
            "equipment_type": "机器人",
        }
        conf = service._calculate_extraction_confidence(project_data)
        assert conf == 0.9

    def test_generate_quality_assessment_high(self):
        """高置信度评估"""
        service, _ = _make_service()
        from app.schemas.presale_ai_knowledge import KnowledgeCaseCreate
        case = KnowledgeCaseCreate(case_name="测试")
        msg = service._generate_quality_assessment(case, 0.85)
        assert "高质量" in msg

    def test_generate_quality_assessment_low(self):
        """低置信度评估"""
        service, _ = _make_service()
        from app.schemas.presale_ai_knowledge import KnowledgeCaseCreate
        case = KnowledgeCaseCreate(case_name="测试")
        msg = service._generate_quality_assessment(case, 0.3)
        assert "低质量" in msg

    def test_calculate_qa_confidence_empty(self):
        """空案例列表置信度为0"""
        service, _ = _make_service()
        conf = service._calculate_qa_confidence([])
        assert conf == 0.0

    def test_calculate_qa_confidence_with_cases(self):
        """有案例时置信度大于0"""
        service, _ = _make_service()
        cases = [_make_mock_case(quality_score=0.8), _make_mock_case(quality_score=0.9)]
        conf = service._calculate_qa_confidence(cases)
        assert conf > 0.0
