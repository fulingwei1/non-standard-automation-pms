# -*- coding: utf-8 -*-
"""
知识贡献端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.knowledge_contribution_service import KnowledgeContributionService
from app.schemas.engineer_performance import (
    KnowledgeContributionCreate, KnowledgeContributionUpdate, KnowledgeReuseCreate
)
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/knowledge", tags=["知识贡献"])


@router.get("", summary="获取知识贡献列表")
async def list_contributions(
    contributor_id: Optional[int] = Query(None, description="贡献者ID"),
    job_type: Optional[str] = Query(None, description="岗位领域"),
    contribution_type: Optional[str] = Query(None, description="贡献类型"),
    status: Optional[str] = Query(None, description="状态"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识贡献列表"""
    service = KnowledgeContributionService(db)

    contributions, total = service.list_contributions(
        contributor_id=contributor_id,
        job_type=job_type,
        contribution_type=contribution_type,
        status=status,
        limit=limit,
        offset=offset
    )

    items = []
    for c in contributions:
        contributor = db.query(User).filter(User.id == c.contributor_id).first()
        items.append({
            "id": c.id,
            "contributor_id": c.contributor_id,
            "contributor_name": contributor.name if contributor else None,
            "contribution_type": c.contribution_type,
            "job_type": c.job_type,
            "title": c.title,
            "description": c.description,
            "tags": c.tags,
            "reuse_count": c.reuse_count,
            "rating_score": float(c.rating_score) if c.rating_score else None,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": total,
            "items": items
        }
    )


@router.post("", summary="创建知识贡献")
async def create_contribution(
    data: KnowledgeContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建知识贡献"""
    service = KnowledgeContributionService(db)
    contribution = service.create_contribution(data, current_user.id)

    return ResponseModel(
        code=200,
        message="创建成功",
        data={"id": contribution.id}
    )


@router.get("/{contribution_id}", summary="获取知识贡献详情")
async def get_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识贡献详情"""
    service = KnowledgeContributionService(db)
    contribution = service.get_contribution(contribution_id)

    if not contribution:
        raise HTTPException(status_code=404, detail="贡献不存在")

    contributor = db.query(User).filter(User.id == contribution.contributor_id).first()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": contribution.id,
            "contributor_id": contribution.contributor_id,
            "contributor_name": contributor.name if contributor else None,
            "contribution_type": contribution.contribution_type,
            "job_type": contribution.job_type,
            "title": contribution.title,
            "description": contribution.description,
            "file_path": contribution.file_path,
            "tags": contribution.tags,
            "reuse_count": contribution.reuse_count,
            "rating_score": float(contribution.rating_score) if contribution.rating_score else None,
            "rating_count": contribution.rating_count,
            "status": contribution.status,
            "approved_by": contribution.approved_by,
            "approved_at": contribution.approved_at.isoformat() if contribution.approved_at else None,
            "created_at": contribution.created_at.isoformat() if contribution.created_at else None
        }
    )


@router.put("/{contribution_id}", summary="更新知识贡献")
async def update_contribution(
    contribution_id: int,
    data: KnowledgeContributionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新知识贡献"""
    service = KnowledgeContributionService(db)

    try:
        contribution = service.update_contribution(contribution_id, data, current_user.id)
        if not contribution:
            raise HTTPException(status_code=404, detail="贡献不存在")
        return ResponseModel(
            code=200,
            message="更新成功",
            data={"id": contribution.id}
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{contribution_id}/submit", summary="提交审核")
async def submit_for_review(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交知识贡献进行审核"""
    service = KnowledgeContributionService(db)

    try:
        contribution = service.submit_for_review(contribution_id, current_user.id)
        return ResponseModel(
            code=200,
            message="已提交审核",
            data={"id": contribution.id, "status": contribution.status}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{contribution_id}/approve", summary="审核通过")
async def approve_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审核通过知识贡献"""
    service = KnowledgeContributionService(db)

    try:
        contribution = service.approve_contribution(contribution_id, current_user.id, True)
        return ResponseModel(
            code=200,
            message="审核通过",
            data={"id": contribution.id, "status": contribution.status}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contribution_id}/reject", summary="审核拒绝")
async def reject_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝知识贡献"""
    service = KnowledgeContributionService(db)

    try:
        contribution = service.approve_contribution(contribution_id, current_user.id, False)
        return ResponseModel(
            code=200,
            message="已拒绝",
            data={"id": contribution.id, "status": contribution.status}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contribution_id}/reuse", summary="记录复用")
async def record_reuse(
    contribution_id: int,
    data: KnowledgeReuseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """记录知识复用"""
    service = KnowledgeContributionService(db)

    # 确保 contribution_id 一致
    data.contribution_id = contribution_id

    try:
        reuse_log = service.record_reuse(data, current_user.id)
        return ResponseModel(
            code=200,
            message="复用已记录",
            data={"id": reuse_log.id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{contribution_id}", summary="删除知识贡献")
async def delete_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识贡献"""
    service = KnowledgeContributionService(db)

    try:
        success = service.delete_contribution(contribution_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="贡献不存在")
        return ResponseModel(
            code=200,
            message="删除成功",
            data=None
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ranking", summary="获取贡献排行")
async def get_contribution_ranking(
    job_type: Optional[str] = Query(None, description="岗位领域"),
    contribution_type: Optional[str] = Query(None, description="贡献类型"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识贡献排行榜"""
    service = KnowledgeContributionService(db)

    ranking = service.get_contribution_ranking(
        job_type=job_type,
        contribution_type=contribution_type,
        limit=limit
    )

    return ResponseModel(
        code=200,
        message="success",
        data=ranking
    )


@router.get("/stats/me", summary="获取我的贡献统计")
async def get_my_contribution_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的贡献统计"""
    service = KnowledgeContributionService(db)
    stats = service.get_contributor_stats(current_user.id)

    return ResponseModel(
        code=200,
        message="success",
        data=stats
    )
