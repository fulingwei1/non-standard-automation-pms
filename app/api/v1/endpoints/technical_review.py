# -*- coding: utf-8 -*-
"""
技术评审管理 API endpoints
包含：评审管理、参与人管理、材料管理、检查项记录、问题管理
"""

from typing import Any, List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.technical_review import (
    TechnicalReview, ReviewParticipant, ReviewMaterial,
    ReviewChecklistRecord, ReviewIssue
)
from app.schemas.technical_review import (
    TechnicalReviewCreate, TechnicalReviewUpdate, TechnicalReviewResponse, TechnicalReviewDetailResponse,
    ReviewParticipantCreate, ReviewParticipantUpdate, ReviewParticipantResponse,
    ReviewMaterialCreate, ReviewMaterialResponse,
    ReviewChecklistRecordCreate, ReviewChecklistRecordUpdate, ReviewChecklistRecordResponse,
    ReviewIssueCreate, ReviewIssueUpdate, ReviewIssueResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_review_no(db: Session, review_type: str) -> str:
    """生成评审编号：RV-{TYPE}-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-{review_type}-{today}-"
    max_review = (
        db.query(TechnicalReview)
        .filter(TechnicalReview.review_no.like(f"{prefix}%"))
        .order_by(desc(TechnicalReview.review_no))
        .first()
    )
    if max_review:
        seq = int(max_review.review_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_issue_no(db: Session) -> str:
    """生成问题编号：RV-ISSUE-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-ISSUE-{today}-"
    max_issue = (
        db.query(ReviewIssue)
        .filter(ReviewIssue.issue_no.like(f"{prefix}%"))
        .order_by(desc(ReviewIssue.issue_no))
        .first()
    )
    if max_issue:
        seq = int(max_issue.issue_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def update_review_issue_counts(db: Session, review_id: int):
    """更新评审问题统计"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        return
    
    issues = db.query(ReviewIssue).filter(ReviewIssue.review_id == review_id).all()
    review.issue_count_a = sum(1 for i in issues if i.issue_level == 'A')
    review.issue_count_b = sum(1 for i in issues if i.issue_level == 'B')
    review.issue_count_c = sum(1 for i in issues if i.issue_level == 'C')
    review.issue_count_d = sum(1 for i in issues if i.issue_level == 'D')
    db.commit()


# ==================== 评审主表 ====================

@router.post("/technical-reviews", response_model=TechnicalReviewResponse, status_code=status.HTTP_201_CREATED)
def create_technical_review(
    review_in: TechnicalReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建技术评审"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == review_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证设备（如果提供）
    if review_in.equipment_id:
        equipment = db.query(Machine).filter(Machine.id == review_in.equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="设备不存在")
    
    # 生成评审编号
    review_no = generate_review_no(db, review_in.review_type)
    
    # 创建评审
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
    
    if keyword:
        query = query.filter(
            or_(
                TechnicalReview.review_no.like(f"%{keyword}%"),
                TechnicalReview.review_name.like(f"%{keyword}%"),
            )
        )
    
    if review_type:
        query = query.filter(TechnicalReview.review_type == review_type)
    
    if project_id:
        query = query.filter(TechnicalReview.project_id == project_id)
    
    if status:
        query = query.filter(TechnicalReview.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    reviews = query.order_by(desc(TechnicalReview.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for review in reviews:
        items.append(TechnicalReviewResponse(
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
        ))
    
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
    
    # 获取关联数据
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
            id=p.id,
            review_id=p.review_id,
            user_id=p.user_id,
            role=p.role,
            is_required=p.is_required,
            attendance=p.attendance,
            delegate_id=p.delegate_id,
            sign_time=p.sign_time,
            signature=p.signature,
            created_at=p.created_at,
        ) for p in participants],
        materials=[ReviewMaterialResponse(
            id=m.id,
            review_id=m.review_id,
            material_type=m.material_type,
            material_name=m.material_name,
            file_path=m.file_path,
            file_size=m.file_size,
            version=m.version,
            is_required=m.is_required,
            upload_by=m.upload_by,
            upload_at=m.upload_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        ) for m in materials],
        checklist_records=[ReviewChecklistRecordResponse(
            id=c.id,
            review_id=c.review_id,
            checklist_item_id=c.checklist_item_id,
            category=c.category,
            check_item=c.check_item,
            result=c.result,
            issue_level=c.issue_level,
            issue_desc=c.issue_desc,
            issue_id=c.issue_id,
            checker_id=c.checker_id,
            remark=c.remark,
            created_at=c.created_at,
        ) for c in checklist_records],
        issues=[ReviewIssueResponse(
            id=i.id,
            review_id=i.review_id,
            issue_no=i.issue_no,
            issue_level=i.issue_level,
            category=i.category,
            description=i.description,
            suggestion=i.suggestion,
            assignee_id=i.assignee_id,
            deadline=i.deadline,
            status=i.status,
            solution=i.solution,
            verify_result=i.verify_result,
            verifier_id=i.verifier_id,
            verify_time=i.verify_time,
            linked_issue_id=i.linked_issue_id,
            created_at=i.created_at,
            updated_at=i.updated_at,
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
    
    # 更新字段
    update_data = review_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    
    # 如果状态变为评审中，记录实际时间
    if review_in.status == 'IN_PROGRESS' and not review.actual_date:
        review.actual_date = datetime.now()
    
    db.commit()
    db.refresh(review)
    
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
    
    # 只有草稿状态才能删除
    if review.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只能删除草稿状态的评审")
    
    db.delete(review)
    db.commit()
    
    return ResponseModel(message="技术评审已删除")


# ==================== 评审参与人 ====================

@router.post("/technical-reviews/{review_id}/participants", response_model=ReviewParticipantResponse, status_code=status.HTTP_201_CREATED)
def create_review_participant(
    review_id: int,
    participant_in: ReviewParticipantCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加评审参与人"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")
    
    # 检查是否已存在
    existing = db.query(ReviewParticipant).filter(
        ReviewParticipant.review_id == review_id,
        ReviewParticipant.user_id == participant_in.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该用户已参与评审")
    
    participant = ReviewParticipant(
        review_id=review_id,
        user_id=participant_in.user_id,
        role=participant_in.role,
        is_required=participant_in.is_required,
    )
    
    db.add(participant)
    db.commit()
    db.refresh(participant)
    
    return ReviewParticipantResponse(
        id=participant.id,
        review_id=participant.review_id,
        user_id=participant.user_id,
        role=participant.role,
        is_required=participant.is_required,
        attendance=participant.attendance,
        delegate_id=participant.delegate_id,
        sign_time=participant.sign_time,
        signature=participant.signature,
        created_at=participant.created_at,
    )


@router.put("/technical-reviews/participants/{participant_id}", response_model=ReviewParticipantResponse, status_code=status.HTTP_200_OK)
def update_review_participant(
    participant_id: int,
    participant_in: ReviewParticipantUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新评审参与人（签到、委派等）"""
    participant = db.query(ReviewParticipant).filter(ReviewParticipant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="评审参与人不存在")
    
    update_data = participant_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(participant, field, value)
    
    # 如果签到，记录签到时间
    if participant_in.attendance == 'CONFIRMED' and not participant.sign_time:
        participant.sign_time = datetime.now()
    
    db.commit()
    db.refresh(participant)
    
    return ReviewParticipantResponse(
        id=participant.id,
        review_id=participant.review_id,
        user_id=participant.user_id,
        role=participant.role,
        is_required=participant.is_required,
        attendance=participant.attendance,
        delegate_id=participant.delegate_id,
        sign_time=participant.sign_time,
        signature=participant.signature,
        created_at=participant.created_at,
    )


@router.delete("/technical-reviews/participants/{participant_id}", status_code=status.HTTP_200_OK)
def delete_review_participant(
    participant_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除评审参与人"""
    participant = db.query(ReviewParticipant).filter(ReviewParticipant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="评审参与人不存在")
    
    db.delete(participant)
    db.commit()
    
    return ResponseModel(message="评审参与人已删除")


# ==================== 评审材料 ====================

@router.post("/technical-reviews/{review_id}/materials", response_model=ReviewMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_review_material(
    review_id: int,
    material_in: ReviewMaterialCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加评审材料"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")
    
    material = ReviewMaterial(
        review_id=review_id,
        material_type=material_in.material_type,
        material_name=material_in.material_name,
        file_path=material_in.file_path,
        file_size=material_in.file_size,
        version=material_in.version,
        is_required=material_in.is_required,
        upload_by=current_user.id,
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return ReviewMaterialResponse(
        id=material.id,
        review_id=material.review_id,
        material_type=material.material_type,
        material_name=material.material_name,
        file_path=material.file_path,
        file_size=material.file_size,
        version=material.version,
        is_required=material.is_required,
        upload_by=material.upload_by,
        upload_at=material.upload_at,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.delete("/technical-reviews/materials/{material_id}", status_code=status.HTTP_200_OK)
def delete_review_material(
    material_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除评审材料"""
    material = db.query(ReviewMaterial).filter(ReviewMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="评审材料不存在")
    
    db.delete(material)
    db.commit()
    
    return ResponseModel(message="评审材料已删除")


# ==================== 评审检查项记录 ====================

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
            assignee_id=record_in.checker_id,  # 默认分配给检查人
            deadline=date.today(),  # 默认今天，后续可修改
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


# ==================== 评审问题 ====================

@router.post("/technical-reviews/{review_id}/issues", response_model=ReviewIssueResponse, status_code=status.HTTP_201_CREATED)
def create_review_issue(
    review_id: int,
    issue_in: ReviewIssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评审问题"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="技术评审不存在")
    
    issue_no = generate_issue_no(db)
    
    issue = ReviewIssue(
        review_id=review_id,
        issue_no=issue_no,
        issue_level=issue_in.issue_level,
        category=issue_in.category,
        description=issue_in.description,
        suggestion=issue_in.suggestion,
        assignee_id=issue_in.assignee_id,
        deadline=issue_in.deadline,
        status='OPEN',
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    # 更新问题统计
    update_review_issue_counts(db, review_id)
    
    return ReviewIssueResponse(
        id=issue.id,
        review_id=issue.review_id,
        issue_no=issue.issue_no,
        issue_level=issue.issue_level,
        category=issue.category,
        description=issue.description,
        suggestion=issue.suggestion,
        assignee_id=issue.assignee_id,
        deadline=issue.deadline,
        status=issue.status,
        solution=issue.solution,
        verify_result=issue.verify_result,
        verifier_id=issue.verifier_id,
        verify_time=issue.verify_time,
        linked_issue_id=issue.linked_issue_id,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@router.put("/technical-reviews/issues/{issue_id}", response_model=ReviewIssueResponse, status_code=status.HTTP_200_OK)
def update_review_issue(
    issue_id: int,
    issue_in: ReviewIssueUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新评审问题"""
    issue = db.query(ReviewIssue).filter(ReviewIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="评审问题不存在")
    
    update_data = issue_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)
    
    # 如果验证，记录验证时间
    if issue_in.verify_result and not issue.verify_time:
        issue.verify_time = datetime.now()
        if not issue.verifier_id:
            issue.verifier_id = current_user.id
    
    db.commit()
    db.refresh(issue)
    
    # 更新问题统计
    update_review_issue_counts(db, issue.review_id)
    
    return ReviewIssueResponse(
        id=issue.id,
        review_id=issue.review_id,
        issue_no=issue.issue_no,
        issue_level=issue.issue_level,
        category=issue.category,
        description=issue.description,
        suggestion=issue.suggestion,
        assignee_id=issue.assignee_id,
        deadline=issue.deadline,
        status=issue.status,
        solution=issue.solution,
        verify_result=issue.verify_result,
        verifier_id=issue.verifier_id,
        verify_time=issue.verify_time,
        linked_issue_id=issue.linked_issue_id,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@router.get("/technical-reviews/issues", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_review_issues(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    review_id: Optional[int] = Query(None, description="评审ID筛选"),
    issue_level: Optional[str] = Query(None, description="问题等级筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    assignee_id: Optional[int] = Query(None, description="责任人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评审问题列表"""
    query = db.query(ReviewIssue)
    
    if review_id:
        query = query.filter(ReviewIssue.review_id == review_id)
    
    if issue_level:
        query = query.filter(ReviewIssue.issue_level == issue_level)
    
    if status:
        query = query.filter(ReviewIssue.status == status)
    
    if assignee_id:
        query = query.filter(ReviewIssue.assignee_id == assignee_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    issues = query.order_by(desc(ReviewIssue.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for issue in issues:
        items.append(ReviewIssueResponse(
            id=issue.id,
            review_id=issue.review_id,
            issue_no=issue.issue_no,
            issue_level=issue.issue_level,
            category=issue.category,
            description=issue.description,
            suggestion=issue.suggestion,
            assignee_id=issue.assignee_id,
            deadline=issue.deadline,
            status=issue.status,
            solution=issue.solution,
            verify_result=issue.verify_result,
            verifier_id=issue.verifier_id,
            verify_time=issue.verify_time,
            linked_issue_id=issue.linked_issue_id,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )






