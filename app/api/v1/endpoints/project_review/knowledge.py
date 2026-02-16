"""
知识库集成API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.project_review import (
    KnowledgeSyncRequest,
    KnowledgeSyncResponse,
    KnowledgeImpactResponse
)
from app.services.project_review_ai import ProjectKnowledgeSyncer

router = APIRouter()


@router.post("/sync", response_model=KnowledgeSyncResponse)
async def sync_to_knowledge_base(
    request: KnowledgeSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步到售前知识库
    
    将项目复盘内容同步到售前知识库，供销售团队参考
    """
    syncer = ProjectKnowledgeSyncer(db)
    
    try:
        result = syncer.sync_to_knowledge_base(
            review_id=request.review_id,
            auto_publish=request.auto_publish
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # 如果包含经验教训，更新知识库案例
    updated_fields = []
    if request.include_lessons and result['success']:
        lesson_result = syncer.update_case_from_lessons(
            review_id=request.review_id,
            case_id=result['knowledge_case_id']
        )
        updated_fields = lesson_result.get('updated_fields', [])
    
    return KnowledgeSyncResponse(
        success=result['success'],
        review_id=request.review_id,
        knowledge_case_id=result['knowledge_case_id'],
        case_name=result['case_name'],
        quality_score=result['quality_score'],
        tags=result.get('sync_log', {}).get('tags', []),
        sync_time=result['sync_log']['sync_time'],
        is_new_case=not bool(updated_fields),
        updated_fields=updated_fields
    )


@router.get("/{review_id}/knowledge-impact", response_model=KnowledgeImpactResponse)
async def get_knowledge_impact(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查看知识库影响
    
    查看该复盘是否已同步到知识库，以及可能的复用场景
    """
    syncer = ProjectKnowledgeSyncer(db)
    sync_status = syncer.get_sync_status(review_id)
    
    # 如果已同步，分析潜在复用场景
    potential_scenarios = None
    similar_cases_count = None
    
    if sync_status.get('synced'):
        # 简单分析：基于标签识别适用场景
        tags = sync_status.get('tags', [])
        potential_scenarios = []
        
        if '高满意度' in tags:
            potential_scenarios.append('客户关系良好的相似项目')
        if '按期交付' in tags:
            potential_scenarios.append('时间紧迫的项目参考')
        if '成本可控' in tags:
            potential_scenarios.append('预算受限的项目借鉴')
        
        # 查询相似案例数量
        from app.models.presale_knowledge_case import PresaleKnowledgeCase
        similar_cases_count = db.query(PresaleKnowledgeCase).filter(
            PresaleKnowledgeCase.id != sync_status.get('case_id'),
            PresaleKnowledgeCase.industry == sync_status.get('industry')
        ).count() if sync_status.get('industry') else 0
    
    return KnowledgeImpactResponse(
        success=True,
        review_id=review_id,
        synced=sync_status.get('synced', False),
        case_id=sync_status.get('case_id'),
        case_name=sync_status.get('case_name'),
        quality_score=sync_status.get('quality_score'),
        tags=sync_status.get('tags'),
        last_updated=sync_status.get('last_updated'),
        potential_reuse_scenarios=potential_scenarios,
        similar_cases_count=similar_cases_count
    )


@router.post("/{review_id}/update-from-lessons")
async def update_knowledge_from_lessons(
    review_id: int,
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从经验教训更新知识库案例"""
    syncer = ProjectKnowledgeSyncer(db)
    
    try:
        result = syncer.update_case_from_lessons(review_id, case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return result
