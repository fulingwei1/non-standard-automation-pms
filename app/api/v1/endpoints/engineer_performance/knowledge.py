# -*- coding: utf-8 -*-
"""
知识贡献端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.engineer_performance import (
    KnowledgeContributionCreate,
    KnowledgeContributionUpdate,
    KnowledgeReuseCreate,
)
from app.services.engineer_performance.engperf_scope import (
    can_view_engineer,
    resolve_engperf_scope,
)
from app.services.knowledge_contribution_service import KnowledgeContributionService

router = APIRouter(prefix="/knowledge", tags=["知识贡献"])


def _resolve_user_display_name(user: Optional[User]) -> Optional[str]:
    if not user:
        return None
    return user.real_name or user.username


def _normalize_tags(tags: Any) -> Optional[list[str]]:
    if tags is None:
        return None
    if isinstance(tags, list):
        cleaned = [str(tag).strip() for tag in tags if str(tag).strip()]
        return cleaned or None
    if isinstance(tags, str):
        normalized = tags.replace("，", ",")
        cleaned = [tag.strip() for tag in normalized.split(",") if tag.strip()]
        return cleaned or None
    return None


def _serialize_contribution(db: Session, contribution: Any) -> dict:
    contributor = db.query(User).filter(User.id == contribution.contributor_id).first()
    return {
        "id": contribution.id,
        "contributor_id": contribution.contributor_id,
        "contributor_name": _resolve_user_display_name(contributor),
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
        "created_at": contribution.created_at.isoformat() if contribution.created_at else None,
    }


@router.get("", summary="获取知识贡献列表")
async def list_contributions(
    contributor_id: Optional[int] = Query(None, description="贡献者ID"),
    job_type: Optional[str] = Query(None, description="岗位领域"),
    contribution_type: Optional[str] = Query(None, description="贡献类型"),
    status: Optional[str] = Query(None, description="状态"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:read")),
):
    """获取知识贡献列表"""
    scope = resolve_engperf_scope(db, current_user)

    # 如果指定了 contributor_id，校验是否有权查看
    if contributor_id is not None:
        target_user = db.query(User).filter(User.id == contributor_id).first()
        target_dept_id = getattr(target_user, "department_id", None) if target_user else None
        if not can_view_engineer(scope, contributor_id, target_dept_id):
            raise HTTPException(status_code=403, detail="无权查看该用户的知识贡献")

    # OWN scope 强制只看自己
    effective_contributor_id = contributor_id
    if scope.scope_type == "OWN" and contributor_id is None:
        effective_contributor_id = current_user.id

    service = KnowledgeContributionService(db)

    contributions, total = service.list_contributions(
        contributor_id=effective_contributor_id,
        job_type=job_type,
        contribution_type=contribution_type,
        status=status,
        limit=pagination.limit,
        offset=pagination.offset
    )

    # 对 TEAM/DEPARTMENT scope 进行后过滤（KnowledgeContribution 无 department_id）
    if scope.scope_type == "TEAM" and scope.accessible_user_ids and contributor_id is None:
        contributions = [c for c in contributions if c.contributor_id in scope.accessible_user_ids]
        total = len(contributions)
    elif scope.scope_type in ("DEPARTMENT", "BUSINESS_UNIT") and scope.accessible_dept_ids and contributor_id is None:
        filtered = []
        for c in contributions:
            u = db.query(User).filter(User.id == c.contributor_id).first()
            if u and getattr(u, "department_id", None) in scope.accessible_dept_ids:
                filtered.append(c)
        contributions = filtered
        total = len(contributions)

    items = [_serialize_contribution(db, contribution) for contribution in contributions]

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
    current_user: User = Depends(security.require_permission("knowledge:write")),
):
    """创建知识贡献"""
    service = KnowledgeContributionService(db)
    contribution = service.create_contribution(data, current_user.id)

    return ResponseModel(
        code=200,
        message="创建成功",
        data={"id": contribution.id}
    )


@router.get("/contributions", summary="获取知识贡献列表（兼容前端）")
async def list_contributions_compat(
    contributor_id: Optional[int] = Query(None, description="贡献者ID"),
    job_type: Optional[str] = Query(None, description="岗位领域"),
    contribution_type: Optional[str] = Query(None, description="贡献类型"),
    status: Optional[str] = Query(None, description="状态"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:read")),
):
    """兼容前端 /knowledge/contributions 调用"""
    scope = resolve_engperf_scope(db, current_user)

    if contributor_id is not None:
        target_user = db.query(User).filter(User.id == contributor_id).first()
        target_dept_id = getattr(target_user, "department_id", None) if target_user else None
        if not can_view_engineer(scope, contributor_id, target_dept_id):
            raise HTTPException(status_code=403, detail="无权查看该用户的知识贡献")

    effective_contributor_id = contributor_id
    if scope.scope_type == "OWN" and contributor_id is None:
        effective_contributor_id = current_user.id

    service = KnowledgeContributionService(db)
    contributions, total = service.list_contributions(
        contributor_id=effective_contributor_id,
        job_type=job_type,
        contribution_type=contribution_type,
        status=status,
        limit=limit,
        offset=offset
    )

    if scope.scope_type == "TEAM" and scope.accessible_user_ids and contributor_id is None:
        contributions = [c for c in contributions if c.contributor_id in scope.accessible_user_ids]
        total = len(contributions)
    elif scope.scope_type in ("DEPARTMENT", "BUSINESS_UNIT") and scope.accessible_dept_ids and contributor_id is None:
        filtered = []
        for c in contributions:
            u = db.query(User).filter(User.id == c.contributor_id).first()
            if u and getattr(u, "department_id", None) in scope.accessible_dept_ids:
                filtered.append(c)
        contributions = filtered
        total = len(contributions)

    items = [_serialize_contribution(db, contribution) for contribution in contributions]
    return ResponseModel(
        code=200,
        message="success",
        data={"total": total, "items": items}
    )


@router.post("/contributions", summary="创建知识贡献（兼容前端）")
async def create_contribution_compat(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:write")),
):
    """兼容前端 /knowledge/contributions 创建调用"""
    try:
        data = KnowledgeContributionCreate(
            contribution_type=payload.get("contribution_type"),
            job_type=payload.get("job_type"),
            title=payload.get("title"),
            description=payload.get("description"),
            file_path=payload.get("file_path"),
            tags=_normalize_tags(payload.get("tags")),
        )
    except (ValidationError, ValueError, TypeError) as exc:
        # Pydantic 验证失败或类型转换错误
        raise HTTPException(status_code=400, detail=f"请求参数错误: {exc}") from exc

    service = KnowledgeContributionService(db)
    contribution = service.create_contribution(data, current_user.id)

    # 兼容前端"提交后即待审核"的流程
    try:
        contribution = service.submit_for_review(contribution.id, current_user.id)
    except (ValueError, PermissionError):
        # 提交审核失败时忽略（贡献已创建成功）
        pass

    return ResponseModel(
        code=200,
        message="创建成功",
        data={"id": contribution.id, "status": contribution.status}
    )


@router.put("/contributions/{contribution_id:int}/approve", summary="审核知识贡献（兼容前端）")
async def approve_contribution_compat(
    contribution_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:approve")),
):
    """兼容前端 PUT /knowledge/contributions/{id}/approve"""
    approve_value = payload.get("approve", True)
    approved = str(approve_value).lower() not in {"0", "false", "no", "n"}
    service = KnowledgeContributionService(db)

    try:
        contribution = service.approve_contribution(contribution_id, current_user.id, approved)
        return ResponseModel(
            code=200,
            message="审核通过" if approved else "已驳回",
            data={"id": contribution.id, "status": contribution.status}
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reuse", summary="记录复用（兼容前端）")
async def record_reuse_compat(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:write")),
):
    """兼容前端 POST /knowledge/reuse"""
    try:
        contribution_id = int(payload.get("contribution_id"))
        project_id_raw = payload.get("project_id")
        project_id = int(project_id_raw) if project_id_raw not in (None, "") else None
        rating_raw = payload.get("rating", payload.get("rating_score"))
        rating = int(rating_raw) if rating_raw not in (None, "") else None

        reuse_data = KnowledgeReuseCreate(
            contribution_id=contribution_id,
            project_id=project_id,
            reuse_type=payload.get("reuse_type"),
            rating=rating,
            feedback=payload.get("feedback") or payload.get("usage_note"),
        )
    except (ValidationError, ValueError, TypeError) as exc:
        # Pydantic 验证失败或类型转换错误
        raise HTTPException(status_code=400, detail=f"请求参数错误: {exc}") from exc

    service = KnowledgeContributionService(db)
    try:
        reuse_log = service.record_reuse(reuse_data, current_user.id)
        return ResponseModel(
            code=200,
            message="复用已记录",
            data={"id": reuse_log.id}
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rankings", summary="获取贡献排行（兼容前端）")
async def get_contribution_rankings_compat(
    job_type: Optional[str] = Query(None, description="岗位领域"),
    contribution_type: Optional[str] = Query(None, description="贡献类型"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:read")),
):
    """兼容前端 /knowledge/rankings 调用"""
    scope = resolve_engperf_scope(db, current_user)
    service = KnowledgeContributionService(db)
    ranking = service.get_contribution_ranking(
        job_type=job_type,
        contribution_type=contribution_type,
        limit=limit
    )

    # 按 scope 过滤排行结果
    items = []
    for row in ranking:
        contributor_id = row.get("contributor_id")
        if contributor_id:
            target_user = db.query(User).filter(User.id == contributor_id).first()
            target_dept_id = getattr(target_user, "department_id", None) if target_user else None
            if not can_view_engineer(scope, contributor_id, target_dept_id):
                continue

        stats = service.get_contributor_stats(contributor_id) if contributor_id else {}
        items.append({
            "rank": len(items) + 1,  # 重新编排 scope 内排名
            "user_id": contributor_id,
            "user_name": row.get("contributor_name"),
            "job_type": row.get("job_type"),
            "contribution_count": row.get("contribution_count", 0),
            "total_reuse": row.get("total_reuse", 0),
            "avg_rating": stats.get("avg_rating", 0),
        })

    return ResponseModel(
        code=200,
        message="success",
        data=items
    )


@router.get("/contributor/{contributor_id}/stats", summary="获取贡献者统计（兼容前端）")
async def get_contributor_stats_compat(
    contributor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:read")),
):
    """兼容前端 /knowledge/contributor/{id}/stats 调用"""
    scope = resolve_engperf_scope(db, current_user)

    target_user_id = current_user.id
    if contributor_id.isdigit():
        target_user_id = int(contributor_id)

    # scope 校验
    target_user = db.query(User).filter(User.id == target_user_id).first()
    target_dept_id = getattr(target_user, "department_id", None) if target_user else None

    if not can_view_engineer(scope, target_user_id, target_dept_id):
        raise HTTPException(status_code=403, detail="无权查看该贡献者的统计数据")

    service = KnowledgeContributionService(db)
    stats = service.get_contributor_stats(target_user_id)
    ranking = service.get_contribution_ranking(limit=200)
    rank = next(
        (item.get("rank") for item in ranking if item.get("contributor_id") == target_user_id),
        None
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "contributor_id": target_user_id,
            "contribution_count": stats.get("total_contributions", 0),
            "total_contributions": stats.get("total_contributions", 0),
            "total_reuse": stats.get("total_reuse", 0),
            "avg_rating": stats.get("avg_rating", 0),
            "by_type": stats.get("by_type", {}),
            "rank": rank,
        }
    )


@router.get("/{contribution_id:int}", summary="获取知识贡献详情")
async def get_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:read")),
):
    """获取知识贡献详情"""
    service = KnowledgeContributionService(db)
    contribution = service.get_contribution(contribution_id)

    if not contribution:
        raise HTTPException(status_code=404, detail="贡献不存在")

    # scope 校验：检查是否有权查看该贡献者的数据
    scope = resolve_engperf_scope(db, current_user)
    contributor = db.query(User).filter(User.id == contribution.contributor_id).first()
    target_dept_id = getattr(contributor, "department_id", None) if contributor else None

    if not can_view_engineer(scope, contribution.contributor_id, target_dept_id):
        raise HTTPException(status_code=403, detail="无权查看该知识贡献")

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": contribution.id,
            "contributor_id": contribution.contributor_id,
            "contributor_name": _resolve_user_display_name(contributor),
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


@router.put("/{contribution_id:int}", summary="更新知识贡献")
async def update_contribution(
    contribution_id: int,
    data: KnowledgeContributionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:write")),
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


@router.post("/{contribution_id:int}/submit", summary="提交审核")
async def submit_for_review(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:write")),
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


@router.post("/{contribution_id:int}/approve", summary="审核通过")
async def approve_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:approve")),
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


@router.post("/{contribution_id:int}/reject", summary="审核拒绝")
async def reject_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:approve")),
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


@router.post("/{contribution_id:int}/reuse", summary="记录复用")
async def record_reuse(
    contribution_id: int,
    data: KnowledgeReuseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:write")),
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


@router.delete("/{contribution_id:int}", summary="删除知识贡献")
async def delete_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:write")),
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
    current_user: User = Depends(security.require_permission("knowledge:read")),
):
    """获取知识贡献排行榜"""
    scope = resolve_engperf_scope(db, current_user)
    service = KnowledgeContributionService(db)

    ranking = service.get_contribution_ranking(
        job_type=job_type,
        contribution_type=contribution_type,
        limit=limit
    )

    # 按 scope 过滤
    filtered = []
    for row in ranking:
        contributor_id = row.get("contributor_id")
        if contributor_id:
            target_user = db.query(User).filter(User.id == contributor_id).first()
            target_dept_id = getattr(target_user, "department_id", None) if target_user else None
            if not can_view_engineer(scope, contributor_id, target_dept_id):
                continue
        row["rank"] = len(filtered) + 1
        filtered.append(row)

    return ResponseModel(
        code=200,
        message="success",
        data=filtered
    )


@router.get("/stats/me", summary="获取我的贡献统计")
async def get_my_contribution_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("knowledge:read")),
):
    """获取当前用户的贡献统计"""
    service = KnowledgeContributionService(db)
    stats = service.get_contributor_stats(current_user.id)

    return ResponseModel(
        code=200,
        message="success",
        data=stats
    )
