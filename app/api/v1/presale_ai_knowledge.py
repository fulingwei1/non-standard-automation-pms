"""
售前AI知识库API路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_db
from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
from app.schemas.presale_ai_knowledge import (
    KnowledgeCaseCreate,
    KnowledgeCaseUpdate,
    KnowledgeCaseResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    BestPracticeRequest,
    BestPracticeResponse,
    KnowledgeExtractionRequest,
    KnowledgeExtractionResponse,
    AIQARequest,
    AIQAResponse,
    QAFeedbackRequest,
    TagsResponse,
    KnowledgeBaseSearchRequest,
    KnowledgeBaseSearchResponse,
)

router = APIRouter(prefix="/api/v1/presale/ai", tags=["售前AI知识库"])


def get_ai_service(db: Session = Depends(get_db)) -> PresaleAIKnowledgeService:
    """获取AI服务实例"""
    return PresaleAIKnowledgeService(db)


# ============= 语义搜索相似案例 =============

@router.post(
    "/search-similar-cases",
    response_model=SemanticSearchResponse,
    summary="语义搜索相似案例",
    description="基于需求语义搜索历史项目，支持多维度筛选"
)
def search_similar_cases(
    request: SemanticSearchRequest,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """语义搜索相似案例"""
    try:
        cases, total = service.semantic_search(request)
        
        return SemanticSearchResponse(
            cases=[KnowledgeCaseResponse(**case.to_dict(), similarity_score=getattr(case, 'similarity_score', None)) 
                   for case in cases],
            total=total,
            query=request.query,
            search_method="semantic"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语义搜索失败: {str(e)}"
        )


# ============= 获取案例详情 =============

@router.get(
    "/case/{case_id}",
    response_model=KnowledgeCaseResponse,
    summary="获取案例详情",
    description="根据ID获取单个案例的完整信息"
)
def get_case(
    case_id: int,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """获取案例详情"""
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"案例不存在: {case_id}"
        )
    
    return KnowledgeCaseResponse(**case.to_dict())


# ============= 推荐最佳实践 =============

@router.post(
    "/recommend-best-practices",
    response_model=BestPracticeResponse,
    summary="推荐最佳实践",
    description="基于场景推荐高质量案例和成功模式"
)
def recommend_best_practices(
    request: BestPracticeRequest,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """推荐最佳实践"""
    try:
        result = service.recommend_best_practices(request)
        
        return BestPracticeResponse(
            recommended_cases=[KnowledgeCaseResponse(**case.to_dict(), similarity_score=getattr(case, 'similarity_score', None))
                              for case in result['recommended_cases']],
            success_pattern_analysis=result['success_pattern_analysis'],
            risk_warnings=result['risk_warnings']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"最佳实践推荐失败: {str(e)}"
        )


# ============= 提取案例知识 =============

@router.post(
    "/extract-case-knowledge",
    response_model=KnowledgeExtractionResponse,
    summary="提取案例知识",
    description="从项目数据中自动提取关键信息并生成案例"
)
def extract_case_knowledge(
    request: KnowledgeExtractionRequest,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """提取案例知识"""
    try:
        result = service.extract_case_knowledge(request)
        
        return KnowledgeExtractionResponse(
            extracted_case=result['extracted_case'],
            extraction_confidence=result['extraction_confidence'],
            suggested_tags=result['suggested_tags'],
            quality_assessment=result['quality_assessment']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识提取失败: {str(e)}"
        )


# ============= 智能问答 =============

@router.post(
    "/qa",
    response_model=AIQAResponse,
    summary="智能问答",
    description="基于知识库的智能问答系统"
)
def ask_question(
    request: AIQARequest,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """智能问答"""
    try:
        result = service.ask_question(request)
        
        return AIQAResponse(
            answer=result['answer'],
            matched_cases=[KnowledgeCaseResponse(**case.to_dict()) 
                          for case in result['matched_cases']],
            confidence_score=result['confidence_score'],
            sources=result['sources']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能问答失败: {str(e)}"
        )


# ============= 知识库搜索 =============

@router.get(
    "/knowledge-base/search",
    response_model=KnowledgeBaseSearchResponse,
    summary="知识库搜索",
    description="支持关键词、标签、行业等多维度搜索"
)
def search_knowledge_base(
    keyword: str = None,
    tags: List[str] = None,
    industry: str = None,
    equipment_type: str = None,
    min_quality_score: float = None,
    page: int = 1,
    page_size: int = 20,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """知识库搜索"""
    try:
        cases, total = service.search_knowledge_base(
            keyword=keyword,
            tags=tags,
            industry=industry,
            equipment_type=equipment_type,
            min_quality_score=min_quality_score,
            page=page,
            page_size=page_size
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return KnowledgeBaseSearchResponse(
            cases=[KnowledgeCaseResponse(**case.to_dict()) for case in cases],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识库搜索失败: {str(e)}"
        )


# ============= 添加案例 =============

@router.post(
    "/knowledge-base/add-case",
    response_model=KnowledgeCaseResponse,
    summary="添加案例",
    description="手动添加案例到知识库"
)
def add_case(
    case_data: KnowledgeCaseCreate,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """添加案例"""
    try:
        case = service.create_case(case_data)
        return KnowledgeCaseResponse(**case.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加案例失败: {str(e)}"
        )


# ============= 更新案例 =============

@router.put(
    "/knowledge-base/case/{case_id}",
    response_model=KnowledgeCaseResponse,
    summary="更新案例",
    description="更新现有案例信息"
)
def update_case(
    case_id: int,
    update_data: KnowledgeCaseUpdate,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """更新案例"""
    case = service.update_case(case_id, update_data)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"案例不存在: {case_id}"
        )
    
    return KnowledgeCaseResponse(**case.to_dict())


# ============= 获取所有标签 =============

@router.get(
    "/knowledge-base/tags",
    response_model=TagsResponse,
    summary="获取所有标签",
    description="获取知识库中所有使用的标签及统计"
)
def get_all_tags(
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """获取所有标签"""
    try:
        result = service.get_all_tags()
        return TagsResponse(
            tags=result['tags'],
            tag_counts=result['tag_counts']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取标签失败: {str(e)}"
        )


# ============= 问答反馈 =============

@router.post(
    "/qa-feedback",
    summary="问答反馈",
    description="提交智能问答的用户反馈"
)
def submit_qa_feedback(
    feedback: QAFeedbackRequest,
    service: PresaleAIKnowledgeService = Depends(get_ai_service)
):
    """问答反馈"""
    success = service.submit_qa_feedback(
        qa_id=feedback.qa_id,
        feedback_score=feedback.feedback_score,
        feedback_comment=feedback.feedback_comment
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"问答记录不存在: {feedback.qa_id}"
        )
    
    return {"message": "反馈已提交", "qa_id": feedback.qa_id}
