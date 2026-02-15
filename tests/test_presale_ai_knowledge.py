"""
售前AI知识库单元测试
总计: 30个测试用例
- 语义搜索测试: 8个
- 案例推荐测试: 6个
- 知识提取测试: 6个
- 智能问答测试: 8个
- 其他功能测试: 2个
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
import numpy as np

from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
from app.models.presale_knowledge_case import PresaleKnowledgeCase
from app.models.presale_ai_qa import PresaleAIQA
from app.schemas.presale_ai_knowledge import (
    KnowledgeCaseCreate,
    KnowledgeCaseUpdate,
    SemanticSearchRequest,
    BestPracticeRequest,
    KnowledgeExtractionRequest,
    AIQARequest,
)


# ============= Fixtures =============

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def ai_service(mock_db):
    """AI服务实例"""
    return PresaleAIKnowledgeService(mock_db)


@pytest.fixture
def sample_case_data():
    """示例案例数据"""
    return KnowledgeCaseCreate(
        case_name="汽车零部件ICT测试项目",
        industry="汽车制造",
        equipment_type="ICT测试设备",
        customer_name="某汽车零部件公司",
        project_amount=500000,
        project_summary="为汽车零部件生产线提供ICT测试解决方案",
        technical_highlights="高精度测试，支持多种PCB规格",
        success_factors="技术方案成熟，团队经验丰富",
        lessons_learned="需要提前确认客户现场环境",
        tags=["ICT测试", "汽车行业", "高精度"],
        quality_score=0.85,
    )


@pytest.fixture
def sample_cases():
    """示例案例列表"""
    cases = []
    for i in range(5):
        case = PresaleKnowledgeCase(
            id=i+1,
            case_name=f"案例{i+1}",
            industry="制造业" if i % 2 == 0 else "电子行业",
            equipment_type="测试设备",
            project_amount=100000 + i * 50000,
            project_summary=f"这是案例{i+1}的摘要",
            quality_score=0.7 + i * 0.05,
            tags=["测试", f"行业{i}"],
        )
        # 添加模拟嵌入
        embedding = np.random.randn(384).astype(np.float32)
        case.embedding = embedding.tobytes()
        cases.append(case)
    return cases


# ============= 语义搜索测试 (8个) =============

def test_semantic_search_basic(ai_service, mock_db, sample_cases):
    """测试1: 基础语义搜索"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = SemanticSearchRequest(query="测试设备", top_k=3)
    cases, total = ai_service.semantic_search(request)
    
    assert len(cases) == 3
    assert total == 5
    assert all(hasattr(c, 'similarity_score') for c in cases)


def test_semantic_search_with_industry_filter(ai_service, mock_db, sample_cases):
    """测试2: 带行业筛选的语义搜索"""
    filtered_cases = [c for c in sample_cases if c.industry == "制造业"]
    mock_db.query.return_value.filter.return_value.all.return_value = filtered_cases
    
    request = SemanticSearchRequest(query="测试", industry="制造业", top_k=5)
    cases, total = ai_service.semantic_search(request)
    
    assert len(cases) <= 5
    assert all(c.industry == "制造业" for c in cases)


def test_semantic_search_with_amount_range(ai_service, mock_db, sample_cases):
    """测试3: 带金额范围筛选的语义搜索"""
    filtered_cases = [c for c in sample_cases if 150000 <= c.project_amount <= 250000]
    mock_db.query.return_value.filter.return_value.all.return_value = filtered_cases
    
    request = SemanticSearchRequest(
        query="测试",
        min_amount=150000,
        max_amount=250000,
        top_k=10
    )
    cases, total = ai_service.semantic_search(request)
    
    assert all(150000 <= c.project_amount <= 250000 for c in cases)


def test_semantic_search_empty_results(ai_service, mock_db):
    """测试4: 无结果的语义搜索"""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    request = SemanticSearchRequest(query="不存在的内容", top_k=10)
    cases, total = ai_service.semantic_search(request)
    
    assert len(cases) == 0
    assert total == 0


def test_semantic_search_similarity_sorting(ai_service, mock_db, sample_cases):
    """测试5: 相似度排序正确性"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = SemanticSearchRequest(query="测试", top_k=5)
    cases, _ = ai_service.semantic_search(request)
    
    # 验证相似度递减
    scores = [c.similarity_score for c in cases]
    assert scores == sorted(scores, reverse=True)


def test_semantic_search_with_equipment_filter(ai_service, mock_db, sample_cases):
    """测试6: 带设备类型筛选的语义搜索"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = SemanticSearchRequest(
        query="测试",
        equipment_type="测试设备",
        top_k=10
    )
    cases, _ = ai_service.semantic_search(request)
    
    assert all(c.equipment_type == "测试设备" for c in cases)


def test_semantic_search_top_k_limit(ai_service, mock_db, sample_cases):
    """测试7: TOP_K限制"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = SemanticSearchRequest(query="测试", top_k=2)
    cases, _ = ai_service.semantic_search(request)
    
    assert len(cases) == 2


def test_semantic_search_without_embedding(ai_service, mock_db):
    """测试8: 无嵌入向量的fallback"""
    # 创建无嵌入的案例
    case_no_embedding = PresaleKnowledgeCase(
        id=1,
        case_name="测试案例",
        project_summary="这是测试摘要",
        embedding=None,
    )
    mock_db.query.return_value.filter.return_value.all.return_value = [case_no_embedding]
    
    request = SemanticSearchRequest(query="测试", top_k=5)
    cases, _ = ai_service.semantic_search(request)
    
    assert len(cases) == 1
    assert cases[0].similarity_score >= 0


# ============= 案例推荐测试 (6个) =============

def test_recommend_best_practices_basic(ai_service, mock_db, sample_cases):
    """测试9: 基础最佳实践推荐"""
    # 设置高质量案例
    for case in sample_cases:
        case.quality_score = 0.8
    
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = BestPracticeRequest(scenario="需要测试设备方案", top_k=3)
    result = ai_service.recommend_best_practices(request)
    
    assert 'recommended_cases' in result
    assert 'success_pattern_analysis' in result
    assert 'risk_warnings' in result
    assert len(result['recommended_cases']) <= 3


def test_recommend_best_practices_high_quality_filter(ai_service, mock_db, sample_cases):
    """测试10: 高质量案例筛选"""
    # 只有部分案例是高质量
    sample_cases[0].quality_score = 0.9
    sample_cases[1].quality_score = 0.85
    sample_cases[2].quality_score = 0.6
    
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = BestPracticeRequest(scenario="测试", top_k=5)
    result = ai_service.recommend_best_practices(request)
    
    # 应该优先推荐高质量案例
    recommended = result['recommended_cases']
    if len(recommended) > 0:
        assert recommended[0].quality_score >= 0.7


def test_recommend_best_practices_with_industry(ai_service, mock_db, sample_cases):
    """测试11: 带行业筛选的推荐"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = BestPracticeRequest(
        scenario="测试方案",
        industry="制造业",
        top_k=3
    )
    result = ai_service.recommend_best_practices(request)
    
    assert 'recommended_cases' in result


def test_recommend_best_practices_success_analysis(ai_service, mock_db, sample_cases):
    """测试12: 成功模式分析"""
    for case in sample_cases:
        case.success_factors = "技术方案准确，团队配合好"
        case.quality_score = 0.8
    
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = BestPracticeRequest(scenario="测试", top_k=3)
    result = ai_service.recommend_best_practices(request)
    
    assert result['success_pattern_analysis']
    assert len(result['success_pattern_analysis']) > 0


def test_recommend_best_practices_risk_warnings(ai_service, mock_db, sample_cases):
    """测试13: 风险警告提取"""
    sample_cases[0].lessons_learned = "注意客户需求确认"
    sample_cases[1].lessons_learned = "提前评估技术风险"
    
    for case in sample_cases:
        case.quality_score = 0.8
    
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = BestPracticeRequest(scenario="测试", top_k=5)
    result = ai_service.recommend_best_practices(request)
    
    assert 'risk_warnings' in result
    assert isinstance(result['risk_warnings'], list)


def test_recommend_best_practices_no_high_quality(ai_service, mock_db, sample_cases):
    """测试14: 无高质量案例时的降级处理"""
    # 所有案例都是低质量
    for case in sample_cases:
        case.quality_score = 0.5
    
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    
    request = BestPracticeRequest(scenario="测试", top_k=3)
    result = ai_service.recommend_best_practices(request)
    
    # 应该返回一些结果，即使质量不高
    assert len(result['recommended_cases']) > 0


# ============= 知识提取测试 (6个) =============

def test_extract_case_knowledge_basic(ai_service, mock_db):
    """测试15: 基础知识提取"""
    project_data = {
        'project_name': '测试项目',
        'description': '这是一个测试项目',
        'industry': '制造业',
        'equipment_type': '测试设备',
        'amount': 200000,
        'status': 'completed',
    }
    
    request = KnowledgeExtractionRequest(project_data=project_data, auto_save=False)
    result = ai_service.extract_case_knowledge(request)
    
    assert 'extracted_case' in result
    assert 'extraction_confidence' in result
    assert 'suggested_tags' in result
    assert 'quality_assessment' in result
    assert result['extracted_case'].case_name == '测试项目'


def test_extract_case_knowledge_auto_save(ai_service, mock_db):
    """测试16: 自动保存知识"""
    project_data = {
        'project_name': '高质量项目',
        'description': '详细描述',
        'industry': '制造业',
        'equipment_type': '设备',
        'technical_highlights': '技术亮点',
        'status': 'completed',
    }
    
    request = KnowledgeExtractionRequest(project_data=project_data, auto_save=True)
    
    # Mock数据库操作
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    result = ai_service.extract_case_knowledge(request)
    
    # 高置信度应该自动保存
    if result['extraction_confidence'] >= 0.7:
        mock_db.add.assert_called_once()


def test_extract_case_knowledge_quality_score(ai_service, mock_db):
    """测试17: 质量评分计算"""
    complete_project = {
        'project_name': '完整项目',
        'description': '详细描述',
        'technical_highlights': '技术亮点',
        'status': 'completed',
    }
    
    incomplete_project = {
        'project_name': '不完整项目',
    }
    
    request1 = KnowledgeExtractionRequest(project_data=complete_project, auto_save=False)
    request2 = KnowledgeExtractionRequest(project_data=incomplete_project, auto_save=False)
    
    result1 = ai_service.extract_case_knowledge(request1)
    result2 = ai_service.extract_case_knowledge(request2)
    
    assert result1['extracted_case'].quality_score > result2['extracted_case'].quality_score


def test_extract_case_knowledge_tags_suggestion(ai_service, mock_db):
    """测试18: 标签建议"""
    project_data = {
        'project_name': '大型项目',
        'industry': '汽车',
        'equipment_type': 'ICT',
        'technology': 'AI',
        'amount': 2000000,
    }
    
    request = KnowledgeExtractionRequest(project_data=project_data, auto_save=False)
    result = ai_service.extract_case_knowledge(request)
    
    tags = result['suggested_tags']
    assert '汽车' in tags
    assert 'ICT' in tags
    assert '大型项目' in tags or 'AI' in tags


def test_extract_case_knowledge_confidence_calculation(ai_service, mock_db):
    """测试19: 置信度计算"""
    high_quality_data = {
        'project_name': '项目名',
        'description': '描述',
        'industry': '行业',
        'equipment_type': '设备',
    }
    
    low_quality_data = {
        'project_name': '项目名',
    }
    
    request1 = KnowledgeExtractionRequest(project_data=high_quality_data, auto_save=False)
    request2 = KnowledgeExtractionRequest(project_data=low_quality_data, auto_save=False)
    
    result1 = ai_service.extract_case_knowledge(request1)
    result2 = ai_service.extract_case_knowledge(request2)
    
    assert result1['extraction_confidence'] > result2['extraction_confidence']


def test_extract_case_knowledge_quality_assessment(ai_service, mock_db):
    """测试20: 质量评估文本"""
    project_data = {
        'project_name': '测试',
        'description': '描述',
        'industry': '行业',
        'equipment_type': '设备',
    }
    
    request = KnowledgeExtractionRequest(project_data=project_data, auto_save=False)
    result = ai_service.extract_case_knowledge(request)
    
    assessment = result['quality_assessment']
    assert isinstance(assessment, str)
    assert len(assessment) > 0
    assert '质量' in assessment or '置信度' in assessment


# ============= 智能问答测试 (8个) =============

def test_ask_question_basic(ai_service, mock_db, sample_cases):
    """测试21: 基础智能问答"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    mock_db.add = Mock()
    mock_db.commit = Mock()
    
    request = AIQARequest(question="如何进行ICT测试？")
    result = ai_service.ask_question(request)
    
    assert 'answer' in result
    assert 'matched_cases' in result
    assert 'confidence_score' in result
    assert 'sources' in result
    assert len(result['answer']) > 0


def test_ask_question_with_context(ai_service, mock_db, sample_cases):
    """测试22: 带上下文的问答"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    mock_db.add = Mock()
    mock_db.commit = Mock()
    
    request = AIQARequest(
        question="需要什么设备？",
        context={'industry': '汽车', 'budget': 500000}
    )
    result = ai_service.ask_question(request)
    
    assert result['answer']
    assert result['confidence_score'] >= 0


def test_ask_question_no_matches(ai_service, mock_db):
    """测试23: 无匹配案例的问答"""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.add = Mock()
    mock_db.commit = Mock()
    
    request = AIQARequest(question="完全不相关的问题")
    result = ai_service.ask_question(request)
    
    assert '未找到相关案例' in result['answer'] or '抱歉' in result['answer']
    assert result['confidence_score'] == 0.0


def test_ask_question_confidence_score(ai_service, mock_db, sample_cases):
    """测试24: 置信度评分计算"""
    # 设置高质量案例
    for case in sample_cases:
        case.quality_score = 0.9
    
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    mock_db.add = Mock()
    mock_db.commit = Mock()
    
    request = AIQARequest(question="测试问题")
    result = ai_service.ask_question(request)
    
    assert 0 <= result['confidence_score'] <= 1
    assert result['confidence_score'] > 0.5  # 有高质量案例时置信度应该较高


def test_ask_question_save_record(ai_service, mock_db, sample_cases):
    """测试25: 问答记录保存"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    mock_db.add = Mock()
    mock_db.commit = Mock()
    
    request = AIQARequest(question="测试问题")
    result = ai_service.ask_question(request, user_id=123)
    
    # 验证数据库add被调用
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_ask_question_sources(ai_service, mock_db, sample_cases):
    """测试26: 信息来源列表"""
    mock_db.query.return_value.filter.return_value.all.return_value = sample_cases
    mock_db.add = Mock()
    mock_db.commit = Mock()
    
    request = AIQARequest(question="测试")
    result = ai_service.ask_question(request)
    
    sources = result['sources']
    assert isinstance(sources, list)
    assert len(sources) <= 3  # 最多3个来源


def test_qa_feedback_submission(ai_service, mock_db):
    """测试27: 问答反馈提交"""
    mock_qa = Mock(spec=PresaleAIQA)
    mock_qa.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_qa
    mock_db.commit = Mock()
    
    success = ai_service.submit_qa_feedback(qa_id=1, feedback_score=5)
    
    assert success is True
    assert mock_qa.feedback_score == 5
    mock_db.commit.assert_called_once()


def test_qa_feedback_not_found(ai_service, mock_db):
    """测试28: 不存在的问答记录反馈"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    success = ai_service.submit_qa_feedback(qa_id=999, feedback_score=5)
    
    assert success is False


# ============= 其他功能测试 (2个) =============

def test_get_all_tags(ai_service, mock_db, sample_cases):
    """测试29: 获取所有标签"""
    mock_db.query.return_value.all.return_value = sample_cases
    
    result = ai_service.get_all_tags()
    
    assert 'tags' in result
    assert 'tag_counts' in result
    assert isinstance(result['tags'], list)
    assert isinstance(result['tag_counts'], dict)


def test_knowledge_base_search_pagination(ai_service, mock_db, sample_cases):
    """测试30: 知识库搜索分页"""
    mock_db.query.return_value.count.return_value = 10
    mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = sample_cases[:2]
    
    cases, total = ai_service.search_knowledge_base(page=1, page_size=2)
    
    assert len(cases) == 2
    assert total == 10


# ============= 运行测试 =============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
