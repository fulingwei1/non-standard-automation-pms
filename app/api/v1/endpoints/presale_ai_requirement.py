"""
AI需求理解API路由
提供6个API端点实现需求分析、精炼、查询等功能
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.presale_ai_requirement import (
    RequirementAnalysisRequest,
    RequirementAnalysisResponse,
    RequirementRefinementRequest,
    RequirementUpdateRequest,
    ClarificationQuestionsResponse,
    ConfidenceScoreResponse,
    ClarificationQuestion
)
from app.services.presale_ai_requirement_service import PresaleAIRequirementService


router = APIRouter(prefix="/api/v1/presale/ai", tags=["presale-ai-requirement"])


@router.post(
    "/analyze-requirement",
    response_model=RequirementAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="分析需求",
    description="""
    使用AI分析客户的原始需求描述，生成结构化需求文档。
    
    **功能**：
    - 提取核心需求和目标
    - 识别设备清单
    - 生成工艺流程
    - 提取技术参数
    - 生成澄清问题
    - 评估技术可行性
    
    **响应时间**：通常 <3秒
    """
)
async def analyze_requirement(
    request: RequirementAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RequirementAnalysisResponse:
    """分析需求"""
    
    try:
        service = PresaleAIRequirementService(db)
        analysis = await service.analyze_requirement(request, current_user.id)
        
        return RequirementAnalysisResponse.from_orm(analysis)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"需求分析失败: {str(e)}"
        )


@router.get(
    "/analysis/{analysis_id}",
    response_model=RequirementAnalysisResponse,
    summary="获取分析结果",
    description="""
    根据分析ID获取完整的需求分析结果。
    
    **返回数据**：
    - 原始需求
    - 结构化需求
    - 设备清单
    - 工艺流程
    - 技术参数
    - 澄清问题
    - 可行性分析
    - 置信度评分
    """
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RequirementAnalysisResponse:
    """获取分析结果"""
    
    service = PresaleAIRequirementService(db)
    analysis = service.get_analysis(analysis_id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"分析记录 {analysis_id} 不存在"
        )
    
    return RequirementAnalysisResponse.from_orm(analysis)


@router.post(
    "/refine-requirement",
    response_model=RequirementAnalysisResponse,
    summary="精炼需求",
    description="""
    基于额外的上下文信息，精炼和深化需求分析。
    
    **使用场景**：
    - 客户提供了补充信息
    - 需要更深入的分析
    - 首次分析置信度较低
    
    **效果**：
    - 更详细的结构化需求
    - 更精确的设备清单
    - 更完整的技术参数
    - 提升置信度评分
    """
)
async def refine_requirement(
    request: RequirementRefinementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RequirementAnalysisResponse:
    """精炼需求"""
    
    try:
        service = PresaleAIRequirementService(db)
        analysis = await service.refine_requirement(request, current_user.id)
        
        return RequirementAnalysisResponse.from_orm(analysis)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"需求精炼失败: {str(e)}"
        )


@router.get(
    "/clarification-questions/{ticket_id}",
    response_model=ClarificationQuestionsResponse,
    summary="获取澄清问题",
    description="""
    获取针对特定售前工单的AI生成澄清问题列表。
    
    **问题分类**：
    - 技术参数
    - 功能需求
    - 约束条件
    - 验收标准
    - 资源预算
    
    **问题优先级**：
    - critical: 必须澄清
    - high: 高度建议
    - medium: 建议澄清
    - low: 可选
    """
)
def get_clarification_questions(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClarificationQuestionsResponse:
    """获取澄清问题"""
    
    service = PresaleAIRequirementService(db)
    questions, analysis_id = service.get_clarification_questions(ticket_id)
    
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工单 {ticket_id} 没有找到澄清问题，请先进行需求分析"
        )
    
    # 统计各优先级问题数量
    critical_count = sum(1 for q in questions if q.importance == "critical")
    high_count = sum(1 for q in questions if q.importance == "high")
    
    return ClarificationQuestionsResponse(
        analysis_id=analysis_id,
        presale_ticket_id=ticket_id,
        questions=questions,
        total_count=len(questions),
        critical_count=critical_count,
        high_priority_count=high_count
    )


@router.post(
    "/update-structured-requirement",
    response_model=RequirementAnalysisResponse,
    summary="更新结构化需求",
    description="""
    手动更新和完善AI生成的结构化需求。
    
    **可更新字段**：
    - structured_requirement: 结构化需求
    - equipment_list: 设备清单
    - process_flow: 工艺流程
    - technical_parameters: 技术参数
    - acceptance_criteria: 验收标准
    
    **用途**：
    - 修正AI的识别错误
    - 补充AI遗漏的信息
    - 根据客户反馈调整需求
    """
)
def update_structured_requirement(
    request: RequirementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RequirementAnalysisResponse:
    """更新结构化需求"""
    
    try:
        service = PresaleAIRequirementService(db)
        analysis = service.update_structured_requirement(request, current_user.id)
        
        return RequirementAnalysisResponse.from_orm(analysis)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.get(
    "/requirement-confidence/{ticket_id}",
    response_model=ConfidenceScoreResponse,
    summary="获取置信度评分",
    description="""
    获取AI需求理解的置信度评分和评估建议。
    
    **置信度等级**：
    - high_confidence (≥0.85): 需求理解充分
    - medium_confidence (0.60-0.84): 需求基本清晰
    - low_confidence (<0.60): 需求信息不足
    
    **评分维度**：
    - 需求完整性 (30%)
    - 技术清晰度 (30%)
    - 参数明确性 (25%)
    - 可执行性 (15%)
    """
)
def get_requirement_confidence(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ConfidenceScoreResponse:
    """获取置信度评分"""
    
    service = PresaleAIRequirementService(db)
    confidence_data = service.get_requirement_confidence(ticket_id)
    
    return ConfidenceScoreResponse(**confidence_data)
