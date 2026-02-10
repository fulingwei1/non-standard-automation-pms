# -*- coding: utf-8 -*-
"""
技术评审主表 CRUD 端点
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter
from app.core.config import settings
from app.models.project import Machine, Project
from app.models.technical_review import TechnicalReview
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.technical_review import (
    ReviewChecklistRecordResponse,
    ReviewIssueResponse,
    ReviewMaterialResponse,
    ReviewParticipantResponse,
    TechnicalReviewCreate,
    TechnicalReviewDetailResponse,
    TechnicalReviewResponse,
    TechnicalReviewUpdate,
)

from .utils import generate_review_no

router = APIRouter()


def _build_review_response(review: TechnicalReview) -> TechnicalReviewResponse:
    """构建评审响应"""
    return TechnicalReviewResponse(
        id=review.id,
        review_no=review.review_no,
        review_type=review.review_type,
        review_name=review.review_name,
        project_id=review.project_id,
        project_no=review.project_no,
        equipment_id=review.equipment_id,
        status=review.status,
        scheduled_date=review.scheduled_date,
        actual_date=review.actual_date,
        location=review.location,
        meeting_type=review.meeting_type,
        host_id=review.host_id,
        presenter_id=review.presenter_id,
        recorder_id=review.recorder_id,
        conclusion=review.conclusion,
        conclusion_summary=review.conclusion_summary,
        condition_deadline=review.condition_deadline,
        next_review_date=review.next_review_date,
        issue_count_a=review.issue_count_a,
        issue_count_b=review.issue_count_b,
        issue_count_c=review.issue_count_c,
        issue_count_d=review.issue_count_d,
        created_by=review.created_by,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.post("/technical-reviews", response_model=TechnicalReviewResponse, status_code=status.HTTP_201_CREATED)
def create_technical_review(
    review_in: TechnicalReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建技术评审"""
    project = db.query(Project).filter(Project.id == review_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if review_in.equipment_id:
        equipment = db.query(Machine).filter(Machine.id == review_in.equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="设备不存在")

    review_no = generate_review_no(db, review_in.review_type)

    review = TechnicalReview(
        review_no=review_no,
        review_type=review_in.review_type,
        review_name=review_in.review_name,
        project_id=review_in.project_id,
        project_no=project.project_code,
        equipment_id=review_in.equipment_id,
        status='DRAFT',
        scheduled_date=review_in.scheduled_date,
        location=review_in.location,
        meeting_type=review_in.meeting_type,
        host_id=review_in.host_id,
        presenter_id=review_in.presenter_id,
        recorder_id=review_in.recorder_id,
        created_by=current_user.id,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return _build_review_response(review)


@router.get("/technical-reviews", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_technical_reviews(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（编号/名称）"),
    review_type: Optional[str] = Query(None, description="评审类型筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取技术评审列表"""
    query = db.query(TechnicalReview)

    query = apply_keyword_filter(query, TechnicalReview, keyword, ["review_no", "review_name"])

    if review_type:
        query = query.filter(TechnicalReview.review_type == review_type)

    if project_id:
        query = query.filter(TechnicalReview.project_id == project_id)

    if status:
        query = query.filter(TechnicalReview.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    reviews = query.order_by(desc(TechnicalReview.created_at)).offset(offset).limit(page_size).all()

    items = [_build_review_response(review) for review in reviews]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/technical-reviews/{review_id}", response_model=TechnicalReviewDetailResponse, status_code=status.HTTP_200_OK)
def read_technical_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取技术评审详情（含关联数据）"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")

    participants = review.participants.all()
    materials = review.materials.all()
    checklist_records = review.checklist_records.all()
    issues = review.issues.all()

    return TechnicalReviewDetailResponse(
        id=review.id,
        review_no=review.review_no,
        review_type=review.review_type,
        review_name=review.review_name,
        project_id=review.project_id,
        project_no=review.project_no,
        equipment_id=review.equipment_id,
        status=review.status,
        scheduled_date=review.scheduled_date,
        actual_date=review.actual_date,
        location=review.location,
        meeting_type=review.meeting_type,
        host_id=review.host_id,
        presenter_id=review.presenter_id,
        recorder_id=review.recorder_id,
        conclusion=review.conclusion,
        conclusion_summary=review.conclusion_summary,
        condition_deadline=review.condition_deadline,
        next_review_date=review.next_review_date,
        issue_count_a=review.issue_count_a,
        issue_count_b=review.issue_count_b,
        issue_count_c=review.issue_count_c,
        issue_count_d=review.issue_count_d,
        created_by=review.created_by,
        created_at=review.created_at,
        updated_at=review.updated_at,
        participants=[ReviewParticipantResponse(
            id=p.id, review_id=p.review_id, user_id=p.user_id, role=p.role,
            is_required=p.is_required, attendance=p.attendance, delegate_id=p.delegate_id,
            sign_time=p.sign_time, signature=p.signature, created_at=p.created_at,
        ) for p in participants],
        materials=[ReviewMaterialResponse(
            id=m.id, review_id=m.review_id, material_type=m.material_type,
            material_name=m.material_name, file_path=m.file_path, file_size=m.file_size,
            version=m.version, is_required=m.is_required, upload_by=m.upload_by,
            upload_at=m.upload_at, created_at=m.created_at, updated_at=m.updated_at,
        ) for m in materials],
        checklist_records=[ReviewChecklistRecordResponse(
            id=c.id, review_id=c.review_id, checklist_item_id=c.checklist_item_id,
            category=c.category, check_item=c.check_item, result=c.result,
            issue_level=c.issue_level, issue_desc=c.issue_desc, issue_id=c.issue_id,
            checker_id=c.checker_id, remark=c.remark, created_at=c.created_at,
        ) for c in checklist_records],
        issues=[ReviewIssueResponse(
            id=i.id, review_id=i.review_id, issue_no=i.issue_no, issue_level=i.issue_level,
            category=i.category, description=i.description, suggestion=i.suggestion,
            assignee_id=i.assignee_id, deadline=i.deadline, status=i.status,
            solution=i.solution, verify_result=i.verify_result, verifier_id=i.verifier_id,
            verify_time=i.verify_time, linked_issue_id=i.linked_issue_id,
            created_at=i.created_at, updated_at=i.updated_at,
        ) for i in issues],
    )


@router.put("/technical-reviews/{review_id}", response_model=TechnicalReviewResponse, status_code=status.HTTP_200_OK)
def update_technical_review(
    review_id: int,
    review_in: TechnicalReviewUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新技术评审"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")

    update_data = review_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    if review_in.status == 'IN_PROGRESS' and not review.actual_date:
        review.actual_date = datetime.now()

    db.commit()
    db.refresh(review)

    # 评审完成时同步到设计评审
    if review_in.status == 'COMPLETED' and review.conclusion:
        try:
            from app.services.design_review_sync_service import DesignReviewSyncService
            sync_service = DesignReviewSyncService(db)
            sync_service.sync_from_technical_review(review.id)
        except Exception as e:
            print(f"设计评审同步失败: {e}")

    return _build_review_response(review)


@router.delete("/technical-reviews/{review_id}", status_code=status.HTTP_200_OK)
def delete_technical_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除技术评审"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")

    if review.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只能删除草稿状态的评审")

    db.delete(review)
    db.commit()

    return ResponseModel(message="技术评审已删除")
