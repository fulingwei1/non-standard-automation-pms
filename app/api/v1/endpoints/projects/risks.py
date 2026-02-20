# -*- coding: utf-8 -*-
"""
项目风险管理 API
包含：风险CRUD、风险矩阵、风险汇总统计
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.project_risk import (
    ProjectRiskCreate,
    ProjectRiskUpdate,
    ProjectRiskResponse,
)
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.services.project_risk import ProjectRiskService

router = APIRouter()


def create_audit_log(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: int,
    details: dict
):
    """创建审计日志 (DISABLED - AuditLog model does not exist)"""
    # FIXME: AuditLog model does not exist, temporarily disabled
    pass


@router.post("/{project_id}/risks", response_model=ResponseModel)
def create_risk(
    project_id: int,
    risk_data: ProjectRiskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("risk:create")),
):
    """
    创建项目风险
    
    需要权限：risk:create
    """
    service = ProjectRiskService(db)
    risk = service.create_risk(
        project_id=project_id,
        risk_name=risk_data.risk_name,
        description=risk_data.description,
        risk_type=risk_data.risk_type,
        probability=risk_data.probability,
        impact=risk_data.impact,
        mitigation_plan=risk_data.mitigation_plan,
        contingency_plan=risk_data.contingency_plan,
        owner_id=risk_data.owner_id,
        target_closure_date=risk_data.target_closure_date,
        current_user=current_user,
    )
    
    # 创建审计日志
    create_audit_log(
        db,
        current_user,
        "CREATE",
        "project_risk",
        risk.id,
        {
            "risk_code": risk.risk_code,
            "risk_name": risk.risk_name,
            "risk_type": risk.risk_type,
            "risk_score": risk.risk_score,
        }
    )
    
    return ResponseModel(
        code=200,
        message="风险创建成功",
        data=ProjectRiskResponse.from_orm(risk).dict()
    )


@router.get("/{project_id}/risks", response_model=ResponseModel)
def get_risks(
    project_id: int,
    risk_type: Optional[str] = Query(None, description="风险类型筛选"),
    risk_level: Optional[str] = Query(None, description="风险等级筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人筛选"),
    is_occurred: Optional[bool] = Query(None, description="是否已发生"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("risk:read")),
):
    """
    获取项目风险列表
    
    需要权限：risk:read
    """
    service = ProjectRiskService(db)
    risks, total = service.get_risk_list(
        project_id=project_id,
        risk_type=risk_type,
        risk_level=risk_level,
        status=status,
        owner_id=owner_id,
        is_occurred=is_occurred,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    
    # 转换为响应格式
    items = [ProjectRiskResponse.from_orm(risk).dict() for risk in risks]
    
    return ResponseModel(
        code=200,
        message="获取风险列表成功",
        data={
            "total": total,
            "items": items,
            "page": pagination.offset // pagination.limit + 1,
            "page_size": pagination.limit,
        }
    )


@router.get("/{project_id}/risks/{risk_id}", response_model=ResponseModel)
def get_risk(
    project_id: int,
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("risk:read")),
):
    """
    获取风险详情
    
    需要权限：risk:read
    """
    service = ProjectRiskService(db)
    risk = service.get_risk_by_id(project_id, risk_id)
    
    return ResponseModel(
        code=200,
        message="获取风险详情成功",
        data=ProjectRiskResponse.from_orm(risk).dict()
    )


@router.put("/{project_id}/risks/{risk_id}", response_model=ResponseModel)
def update_risk(
    project_id: int,
    risk_id: int,
    risk_data: ProjectRiskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("risk:update")),
):
    """
    更新风险信息
    
    需要权限：risk:update
    """
    service = ProjectRiskService(db)
    
    # 获取更新前的状态
    old_risk = service.get_risk_by_id(project_id, risk_id)
    old_data = {
        "risk_score": old_risk.risk_score,
        "risk_level": old_risk.risk_level,
        "status": old_risk.status,
    }
    
    # 更新风险
    update_data = risk_data.dict(exclude_unset=True)
    risk = service.update_risk(
        project_id=project_id,
        risk_id=risk_id,
        update_data=update_data,
        current_user=current_user,
    )
    
    # 创建审计日志
    create_audit_log(
        db,
        current_user,
        "UPDATE",
        "project_risk",
        risk.id,
        {
            "risk_code": risk.risk_code,
            "old_data": old_data,
            "new_data": {
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "status": risk.status,
            },
            "updated_fields": list(update_data.keys()),
        }
    )
    
    return ResponseModel(
        code=200,
        message="风险更新成功",
        data=ProjectRiskResponse.from_orm(risk).dict()
    )


@router.delete("/{project_id}/risks/{risk_id}", response_model=ResponseModel)
def delete_risk(
    project_id: int,
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("risk:delete")),
):
    """
    删除风险
    
    需要权限：risk:delete
    """
    service = ProjectRiskService(db)
    risk_info = service.delete_risk(project_id, risk_id)
    
    # 创建审计日志
    create_audit_log(
        db,
        current_user,
        "DELETE",
        "project_risk",
        risk_info["risk_code"],
        risk_info
    )
    
    return ResponseModel(
        code=200,
        message="风险删除成功",
        data=None
    )


@router.get("/{project_id}/risk-matrix", response_model=ResponseModel)
def get_risk_matrix(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("risk:read")),
):
    """
    获取风险矩阵（概率×影响）
    
    需要权限：risk:read
    
    返回5x5矩阵，每个单元格包含该概率和影响组合的风险数量和列表
    """
    service = ProjectRiskService(db)
    data = service.get_risk_matrix(project_id)
    
    return ResponseModel(
        code=200,
        message="获取风险矩阵成功",
        data=data
    )


@router.get("/{project_id}/risk-summary", response_model=ResponseModel)
def get_risk_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("risk:read")),
):
    """
    获取风险汇总统计
    
    需要权限：risk:read
    
    包含：总数、按类型统计、按等级统计、按状态统计等
    """
    service = ProjectRiskService(db)
    summary = service.get_risk_summary(project_id)
    
    return ResponseModel(
        code=200,
        message="获取风险汇总统计成功",
        data=summary
    )
