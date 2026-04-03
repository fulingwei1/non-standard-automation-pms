# -*- coding: utf-8 -*-
"""
坑点预警 API
新项目创建时自动推送类似项目的历史坑点
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.knowledge_base import KnowledgeAlertFeedback
from app.services.knowledge.pitfall_alert_service import PitfallAlertService

router = APIRouter()


@router.post("/projects/{project_id}/pitfall-alerts", response_model=ResponseModel)
def generate_pitfall_alerts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    为项目生成坑点预警

    自动匹配维度：
    - 同客户的历史坑点
    - 同产品类别的常见风险
    - 同项目类型的经验教训
    - 同行业的通用知识
    """
    service = PitfallAlertService(db)
    result = service.generate_alerts(project_id)

    db.commit()

    alerts_data = [
        {
            "id": a.id,
            "knowledge_entry_id": a.knowledge_entry_id,
            "match_reason": a.match_reason,
            "match_score": a.match_score,
        }
        for a in result["alerts"]
    ]

    return ResponseModel(
        code=200,
        message=f"生成 {result['alerts_generated']} 条坑点预警",
        data={
            "target_project_id": result["target_project_id"],
            "alerts_generated": result["alerts_generated"],
            "alerts": alerts_data,
        },
    )


@router.get("/projects/{project_id}/pitfall-alerts", response_model=ResponseModel)
def get_project_alerts(
    project_id: int,
    unread_only: bool = Query(False, description="仅显示未读"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目的坑点预警列表"""
    service = PitfallAlertService(db)
    result = service.get_project_alerts(
        project_id, unread_only=unread_only, page=page, page_size=page_size
    )

    items_data = []
    for a in result["items"]:
        entry = a.knowledge_entry
        items_data.append({
            "id": a.id,
            "knowledge_entry_id": a.knowledge_entry_id,
            "match_reason": a.match_reason,
            "match_score": a.match_score,
            "is_read": a.is_read,
            "is_adopted": a.is_adopted,
            "entry_title": entry.title if entry else None,
            "entry_summary": entry.summary if entry else None,
            "entry_type": (
                entry.knowledge_type.value
                if entry and hasattr(entry.knowledge_type, "value")
                else str(entry.knowledge_type) if entry else None
            ),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={"total": result["total"], "items": items_data},
    )


@router.put("/pitfall-alerts/{alert_id}/read", response_model=ResponseModel)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """标记预警已读"""
    service = PitfallAlertService(db)
    service.mark_read(alert_id)
    db.commit()
    return ResponseModel(code=200, message="已标记为已读")


@router.put("/pitfall-alerts/{alert_id}/feedback", response_model=ResponseModel)
def submit_alert_feedback(
    alert_id: int,
    body: KnowledgeAlertFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """提交预警反馈（是否采纳）"""
    service = PitfallAlertService(db)
    service.submit_feedback(alert_id, is_adopted=body.is_adopted, feedback=body.feedback)
    db.commit()
    return ResponseModel(code=200, message="反馈已提交")
