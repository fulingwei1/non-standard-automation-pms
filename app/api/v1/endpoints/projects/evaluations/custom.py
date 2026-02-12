# -*- coding: utf-8 -*-
"""
项目评价自定义端点

包含最新评价查询、确认评价等功能
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project_evaluation import ProjectEvaluationResponse
from app.services.project_evaluation_service import ProjectEvaluationService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/latest", response_model=ResponseModel[ProjectEvaluationResponse])
def get_project_latest_evaluation(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """获取项目最新评价"""
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    eval_service = ProjectEvaluationService(db)
    evaluation = eval_service.get_latest_evaluation(project_id)
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="项目暂无评价记录")
    
    return ResponseModel(code=200, data=evaluation)


@router.post("/{eval_id}/confirm", response_model=ResponseModel[ProjectEvaluationResponse])
def confirm_project_evaluation(
    project_id: int = Path(..., description="项目ID"),
    eval_id: int = Path(..., description="评价ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:update")),
) -> Any:
    """确认项目评价（将状态改为CONFIRMED）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    evaluation = db.query(ProjectEvaluation).filter(
        ProjectEvaluation.id == eval_id,
        ProjectEvaluation.project_id == project_id,
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")
    
    evaluation.status = "CONFIRMED"
    db.commit()
    db.refresh(evaluation)
    
    return ResponseModel(code=200, message="确认成功", data=evaluation)
