# -*- coding: utf-8 -*-
"""
评审检查项记录端点
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.technical_review import ReviewChecklistRecord, ReviewIssue, TechnicalReview
from app.models.user import User
from app.schemas.technical_review import (
    ReviewChecklistRecordCreate,
    ReviewChecklistRecordResponse,
    ReviewChecklistRecordUpdate,
)

from .utils import generate_issue_no, update_review_issue_counts

router = APIRouter()


@router.post("/technical-reviews/{review_id}/checklist-records", response_model=ReviewChecklistRecordResponse, status_code=status.HTTP_201_CREATED)
def create_checklist_record(
    review_id: int,
    record_in: ReviewChecklistRecordCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评审检查项记录"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")

    record = ReviewChecklistRecord(
        review_id=review_id,
        checklist_item_id=record_in.checklist_item_id,
        category=record_in.category,
        check_item=record_in.check_item,
        result=record_in.result,
        issue_level=record_in.issue_level,
        issue_desc=record_in.issue_desc,
        checker_id=record_in.checker_id,
        remark=record_in.remark,
    )

    db.add(record)

    # 如果不通过，自动创建问题
    if record_in.result == 'FAIL' and record_in.issue_level and record_in.issue_desc:
        issue_no = generate_issue_no(db)
        issue = ReviewIssue(
            review_id=review_id,
            issue_no=issue_no,
            issue_level=record_in.issue_level,
            category=record_in.category,
            description=record_in.issue_desc,
            assignee_id=record_in.checker_id,
            deadline=date.today(),
            status='OPEN',
        )
        db.add(issue)
        db.flush()
        record.issue_id = issue.id

    db.commit()
    db.refresh(record)

    # 更新问题统计
    update_review_issue_counts(db, review_id)

    return ReviewChecklistRecordResponse(
        id=record.id,
        review_id=record.review_id,
        checklist_item_id=record.checklist_item_id,
        category=record.category,
        check_item=record.check_item,
        result=record.result,
        issue_level=record.issue_level,
        issue_desc=record.issue_desc,
        issue_id=record.issue_id,
        checker_id=record.checker_id,
        remark=record.remark,
        created_at=record.created_at,
    )


@router.put("/technical-reviews/checklist-records/{record_id}", response_model=ReviewChecklistRecordResponse, status_code=status.HTTP_200_OK)
def update_checklist_record(
    record_id: int,
    record_in: ReviewChecklistRecordUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新评审检查项记录"""
    record = db.query(ReviewChecklistRecord).filter(ReviewChecklistRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="检查项记录不存在")

    update_data = record_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)

    return ReviewChecklistRecordResponse(
        id=record.id,
        review_id=record.review_id,
        checklist_item_id=record.checklist_item_id,
        category=record.category,
        check_item=record.check_item,
        result=record.result,
        issue_level=record.issue_level,
        issue_desc=record.issue_desc,
        issue_id=record.issue_id,
        checker_id=record.checker_id,
        remark=record.remark,
        created_at=record.created_at,
    )
