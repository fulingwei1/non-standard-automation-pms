"""
项目经验教训API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project_review import ProjectLesson
from app.schemas.project_review import (
    ProjectLessonCreate,
    ProjectLessonUpdate,
    ProjectLessonResponse,
    LessonExtractRequest,
    LessonExtractResponse
)
from app.services.project_review_ai import ProjectLessonExtractor
from datetime import datetime

router = APIRouter()


@router.post("/extract", response_model=LessonExtractResponse)
async def extract_lessons(
    request: LessonExtractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI提取经验教训
    
    从复盘报告中自动识别和提取结构化的经验教训
    """
    start_time = datetime.now()
    
    # 1. 提取经验教训
    extractor = ProjectLessonExtractor(db)
    lessons_data = extractor.extract_lessons(
        review_id=request.review_id,
        min_confidence=request.min_confidence
    )
    
    # 2. 保存到数据库（如果启用）
    saved_lessons = []
    if request.auto_save:
        for lesson_data in lessons_data:
            lesson = ProjectLesson(**lesson_data)
            db.add(lesson)
            saved_lessons.append(lesson)
        
        db.commit()
        for lesson in saved_lessons:
            db.refresh(lesson)
    
    # 3. 计算处理时间
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return LessonExtractResponse(
        success=True,
        review_id=request.review_id,
        extracted_count=len(lessons_data),
        saved_count=len(saved_lessons),
        lessons=[ProjectLessonResponse.from_orm(l) for l in saved_lessons],
        processing_time_ms=processing_time
    )


@router.get("", response_model=List[ProjectLessonResponse])
async def list_lessons(
    review_id: Optional[int] = None,
    project_id: Optional[int] = None,
    lesson_type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取经验教训列表
    
    支持多维度筛选
    """
    query = db.query(ProjectLesson)
    
    if review_id:
        query = query.filter(ProjectLesson.review_id == review_id)
    if project_id:
        query = query.filter(ProjectLesson.project_id == project_id)
    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)
    if category:
        query = query.filter(ProjectLesson.category == category)
    if status:
        query = query.filter(ProjectLesson.status == status)
    if min_confidence is not None:
        query = query.filter(ProjectLesson.ai_confidence >= min_confidence)
    
    lessons = query.order_by(
        ProjectLesson.priority.desc(),
        ProjectLesson.ai_confidence.desc()
    ).offset(skip).limit(limit).all()
    
    return [ProjectLessonResponse.from_orm(lesson) for lesson in lessons]


@router.get("/{lesson_id}", response_model=ProjectLessonResponse)
async def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取经验教训详情"""
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")
    
    return ProjectLessonResponse.from_orm(lesson)


@router.patch("/{lesson_id}", response_model=ProjectLessonResponse)
async def update_lesson(
    lesson_id: int,
    update_data: ProjectLessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新经验教训"""
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")
    
    # 更新字段
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(lesson, key, value)
    
    db.commit()
    db.refresh(lesson)
    
    return ProjectLessonResponse.from_orm(lesson)


@router.get("/{lesson_id}/similar")
async def get_similar_lessons(
    lesson_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查找相似的历史经验"""
    extractor = ProjectLessonExtractor(db)
    similar_lessons = extractor.find_similar_lessons(lesson_id, limit)
    
    return {
        "lesson_id": lesson_id,
        "similar_lessons": similar_lessons,
        "count": len(similar_lessons)
    }


@router.get("/categorize/by-category")
async def categorize_lessons(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """按类别分组经验教训"""
    lessons = db.query(ProjectLesson).filter(
        ProjectLesson.review_id == review_id
    ).all()
    
    extractor = ProjectLessonExtractor(db)
    categorized = extractor.categorize_lessons([
        {
            'id': l.id,
            'category': l.category,
            'title': l.title,
            'lesson_type': l.lesson_type,
            'ai_confidence': float(l.ai_confidence or 0)
        }
        for l in lessons
    ])
    
    return {
        "review_id": review_id,
        "categorized": categorized,
        "total_count": len(lessons)
    }
