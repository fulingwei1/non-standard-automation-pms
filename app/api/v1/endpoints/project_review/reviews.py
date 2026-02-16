"""
项目复盘报告API端点
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.project_review import ProjectReview
from app.schemas.project_review import (
    ProjectReviewCreate,
    ProjectReviewUpdate,
    ProjectReviewResponse,
    ProjectReviewListResponse,
    ReviewGenerateRequest,
    ReviewGenerateResponse
)
from app.services.project_review_ai import (
    ProjectReviewReportGenerator,
    ProjectLessonExtractor,
    ProjectKnowledgeSyncer
)

router = APIRouter()


@router.post("/generate", response_model=ReviewGenerateResponse)
async def generate_review_report(
    request: ReviewGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI生成项目复盘报告
    
    - **project_id**: 项目ID
    - **review_type**: 复盘类型（POST_MORTEM/MID_TERM/QUARTERLY）
    - **auto_extract_lessons**: 是否自动提取经验教训
    - **auto_sync_knowledge**: 是否自动同步到知识库
    """
    start_time = datetime.now()
    
    # 1. 生成复盘报告
    generator = ProjectReviewReportGenerator(db)
    report_data = generator.generate_report(
        project_id=request.project_id,
        review_type=request.review_type,
        additional_context=request.additional_context
    )
    
    # 2. 生成复盘编号
    review_no = f"REV{datetime.now().strftime('%Y%m%d')}{request.project_id:04d}"
    
    # 3. 创建复盘记录
    review = ProjectReview(
        review_no=review_no,
        reviewer_id=request.reviewer_id,
        reviewer_name=current_user.username,
        **report_data
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # 4. 自动提取经验教训（如果启用）
    extracted_lessons_count = None
    if request.auto_extract_lessons:
        extractor = ProjectLessonExtractor(db)
        lessons = extractor.extract_lessons(review.id, min_confidence=0.6)
        
        from app.models.project_review import ProjectLesson
        for lesson_data in lessons:
            lesson = ProjectLesson(**lesson_data)
            db.add(lesson)
        db.commit()
        extracted_lessons_count = len(lessons)
    
    # 5. 自动同步到知识库（如果启用）
    synced_to_knowledge = None
    knowledge_case_id = None
    if request.auto_sync_knowledge:
        syncer = ProjectKnowledgeSyncer(db)
        sync_result = syncer.sync_to_knowledge_base(review.id)
        synced_to_knowledge = sync_result['success']
        knowledge_case_id = sync_result.get('knowledge_case_id')
    
    # 6. 计算处理时间
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return ReviewGenerateResponse(
        success=True,
        review_id=review.id,
        review_no=review.review_no,
        processing_time_ms=processing_time,
        ai_summary=report_data.get('ai_summary', ''),
        extracted_lessons_count=extracted_lessons_count,
        synced_to_knowledge=synced_to_knowledge,
        knowledge_case_id=knowledge_case_id
    )


@router.get("", response_model=ProjectReviewListResponse)
async def list_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    review_type: Optional[str] = None,
    ai_generated: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取复盘报告列表
    
    - **skip**: 跳过记录数
    - **limit**: 返回记录数
    - **project_id**: 按项目筛选
    - **status**: 按状态筛选
    - **review_type**: 按复盘类型筛选
    - **ai_generated**: 按AI生成标记筛选
    """
    query = db.query(ProjectReview)
    
    if project_id:
        query = query.filter(ProjectReview.project_id == project_id)
    if status:
        query = query.filter(ProjectReview.status == status)
    if review_type:
        query = query.filter(ProjectReview.review_type == review_type)
    if ai_generated is not None:
        query = query.filter(ProjectReview.ai_generated == ai_generated)
    
    total = query.count()
    items = query.order_by(ProjectReview.created_at.desc()).offset(skip).limit(limit).all()
    
    return ProjectReviewListResponse(
        total=total,
        items=[ProjectReviewResponse.from_orm(item) for item in items]
    )


@router.get("/{review_id}", response_model=ProjectReviewResponse)
async def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取复盘报告详情"""
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    return ProjectReviewResponse.from_orm(review)


@router.patch("/{review_id}", response_model=ProjectReviewResponse)
async def update_review(
    review_id: int,
    update_data: ProjectReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新复盘报告"""
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(review, key, value)
    
    db.commit()
    db.refresh(review)
    
    return ProjectReviewResponse.from_orm(review)


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除复盘报告"""
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")
    
    db.delete(review)
    db.commit()
    
    return {"success": True, "message": "复盘报告已删除"}


@router.get("/stats/summary")
async def get_review_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取复盘统计信息"""
    from sqlalchemy import func
    
    total_reviews = db.query(func.count(ProjectReview.id)).scalar()
    ai_generated_count = db.query(func.count(ProjectReview.id)).filter(
        ProjectReview.ai_generated == True
    ).scalar()
    
    avg_quality_score = db.query(func.avg(ProjectReview.quality_score)).filter(
        ProjectReview.quality_score.isnot(None)
    ).scalar()
    
    by_type = db.query(
        ProjectReview.review_type,
        func.count(ProjectReview.id)
    ).group_by(ProjectReview.review_type).all()
    
    by_status = db.query(
        ProjectReview.status,
        func.count(ProjectReview.id)
    ).group_by(ProjectReview.status).all()
    
    return {
        "total_reviews": total_reviews,
        "ai_generated_count": ai_generated_count,
        "ai_generated_ratio": ai_generated_count / total_reviews if total_reviews > 0 else 0,
        "average_quality_score": float(avg_quality_score) if avg_quality_score else 0,
        "by_type": {type_: count for type_, count in by_type},
        "by_status": {status: count for status, count in by_status}
    }
