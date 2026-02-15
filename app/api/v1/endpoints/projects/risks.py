# -*- coding: utf-8 -*-
"""
项目风险管理 API
包含：风险CRUD、风险矩阵、风险汇总统计
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user, require_permission
from app.models.project_risk import ProjectRisk, RiskTypeEnum, RiskStatusEnum
from app.models.project import Project
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.project_risk import (
    ProjectRiskCreate,
    ProjectRiskUpdate,
    ProjectRiskResponse,
    RiskMatrixResponse,
    RiskSummaryResponse,
    RiskMatrixItem,
)
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination

router = APIRouter()


def create_audit_log(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: int,
    details: dict
):
    """创建审计日志"""
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address="",  # 可以从请求中获取
        user_agent="",  # 可以从请求中获取
    )
    db.add(audit)
    db.commit()


@router.post("/projects/{project_id}/risks", response_model=ResponseModel)
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
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 生成风险编号
    count = db.query(ProjectRisk).filter(ProjectRisk.project_id == project_id).count()
    risk_code = f"RISK-{project.project_code}-{count + 1:04d}"
    
    # 创建风险对象
    risk = ProjectRisk(
        risk_code=risk_code,
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
        status=RiskStatusEnum.IDENTIFIED,
        created_by_id=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )
    
    # 如果有负责人，设置负责人姓名
    if risk.owner_id:
        owner = db.query(User).filter(User.id == risk.owner_id).first()
        if owner:
            risk.owner_name = owner.real_name or owner.username
    
    # 计算风险评分
    risk.calculate_risk_score()
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
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


@router.get("/projects/{project_id}/risks", response_model=ResponseModel)
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
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 构建查询
    query = db.query(ProjectRisk).filter(ProjectRisk.project_id == project_id)
    
    # 应用筛选
    if risk_type:
        query = query.filter(ProjectRisk.risk_type == risk_type)
    if risk_level:
        query = query.filter(ProjectRisk.risk_level == risk_level)
    if status:
        query = query.filter(ProjectRisk.status == status)
    if owner_id:
        query = query.filter(ProjectRisk.owner_id == owner_id)
    if is_occurred is not None:
        query = query.filter(ProjectRisk.is_occurred == is_occurred)
    
    # 获取总数
    total = query.count()
    
    # 应用分页并排序
    risks = apply_pagination(
        query.order_by(desc(ProjectRisk.risk_score), desc(ProjectRisk.created_at)),
        pagination.offset,
        pagination.limit
    ).all()
    
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


@router.get("/projects/{project_id}/risks/{risk_id}", response_model=ResponseModel)
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
    risk = db.query(ProjectRisk).filter(
        and_(
            ProjectRisk.id == risk_id,
            ProjectRisk.project_id == project_id
        )
    ).first()
    
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    
    return ResponseModel(
        code=200,
        message="获取风险详情成功",
        data=ProjectRiskResponse.from_orm(risk).dict()
    )


@router.put("/projects/{project_id}/risks/{risk_id}", response_model=ResponseModel)
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
    risk = db.query(ProjectRisk).filter(
        and_(
            ProjectRisk.id == risk_id,
            ProjectRisk.project_id == project_id
        )
    ).first()
    
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    
    # 记录更新前的状态
    old_data = {
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level,
        "status": risk.status,
    }
    
    # 更新字段
    update_data = risk_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(risk, field, value)
    
    # 如果概率或影响发生变化，重新计算评分
    if risk_data.probability is not None or risk_data.impact is not None:
        risk.calculate_risk_score()
    
    # 如果负责人变化，更新负责人姓名
    if risk_data.owner_id is not None:
        owner = db.query(User).filter(User.id == risk_data.owner_id).first()
        if owner:
            risk.owner_name = owner.real_name or owner.username
    
    # 更新审计字段
    risk.updated_by_id = current_user.id
    risk.updated_by_name = current_user.real_name or current_user.username
    
    # 如果状态变为已关闭，设置关闭日期
    if risk_data.status == "CLOSED" and not risk.actual_closure_date:
        risk.actual_closure_date = datetime.now()
    
    db.commit()
    db.refresh(risk)
    
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


@router.delete("/projects/{project_id}/risks/{risk_id}", response_model=ResponseModel)
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
    risk = db.query(ProjectRisk).filter(
        and_(
            ProjectRisk.id == risk_id,
            ProjectRisk.project_id == project_id
        )
    ).first()
    
    if not risk:
        raise HTTPException(status_code=404, detail="风险不存在")
    
    # 记录删除信息用于审计
    risk_info = {
        "risk_code": risk.risk_code,
        "risk_name": risk.risk_name,
        "risk_type": risk.risk_type,
        "risk_score": risk.risk_score,
    }
    
    db.delete(risk)
    db.commit()
    
    # 创建审计日志
    create_audit_log(
        db,
        current_user,
        "DELETE",
        "project_risk",
        risk_id,
        risk_info
    )
    
    return ResponseModel(
        code=200,
        message="风险删除成功",
        data=None
    )


@router.get("/projects/{project_id}/risk-matrix", response_model=ResponseModel)
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
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有风险
    risks = db.query(ProjectRisk).filter(
        and_(
            ProjectRisk.project_id == project_id,
            ProjectRisk.status != RiskStatusEnum.CLOSED
        )
    ).all()
    
    # 构建矩阵数据
    matrix_data = {}
    for prob in range(1, 6):
        for imp in range(1, 6):
            key = f"{prob}_{imp}"
            matrix_data[key] = []
    
    # 填充矩阵
    for risk in risks:
        key = f"{risk.probability}_{risk.impact}"
        matrix_data[key].append({
            "id": risk.id,
            "risk_code": risk.risk_code,
            "risk_name": risk.risk_name,
            "risk_type": risk.risk_type,
            "risk_score": risk.risk_score,
            "risk_level": risk.risk_level,
        })
    
    # 转换为列表格式
    matrix = []
    for prob in range(1, 6):
        for imp in range(1, 6):
            key = f"{prob}_{imp}"
            risks_in_cell = matrix_data[key]
            matrix.append({
                "probability": prob,
                "impact": imp,
                "count": len(risks_in_cell),
                "risks": risks_in_cell,
            })
    
    # 计算汇总统计
    summary = {
        "total_risks": len(risks),
        "critical_count": sum(1 for r in risks if r.risk_level == "CRITICAL"),
        "high_count": sum(1 for r in risks if r.risk_level == "HIGH"),
        "medium_count": sum(1 for r in risks if r.risk_level == "MEDIUM"),
        "low_count": sum(1 for r in risks if r.risk_level == "LOW"),
    }
    
    return ResponseModel(
        code=200,
        message="获取风险矩阵成功",
        data={
            "matrix": matrix,
            "summary": summary,
        }
    )


@router.get("/projects/{project_id}/risk-summary", response_model=ResponseModel)
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
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有风险
    risks = db.query(ProjectRisk).filter(ProjectRisk.project_id == project_id).all()
    
    # 按类型统计
    by_type = {}
    for risk_type in RiskTypeEnum:
        count = sum(1 for r in risks if r.risk_type == risk_type)
        by_type[risk_type.value] = count
    
    # 按等级统计
    by_level = {
        "CRITICAL": sum(1 for r in risks if r.risk_level == "CRITICAL"),
        "HIGH": sum(1 for r in risks if r.risk_level == "HIGH"),
        "MEDIUM": sum(1 for r in risks if r.risk_level == "MEDIUM"),
        "LOW": sum(1 for r in risks if r.risk_level == "LOW"),
    }
    
    # 按状态统计
    by_status = {}
    for status in RiskStatusEnum:
        count = sum(1 for r in risks if r.status == status)
        by_status[status.value] = count
    
    # 计算平均风险评分
    avg_score = sum(r.risk_score for r in risks) / len(risks) if risks else 0
    
    # 高优先级风险数量（HIGH + CRITICAL）
    high_priority_count = by_level["HIGH"] + by_level["CRITICAL"]
    
    summary = {
        "total_risks": len(risks),
        "by_type": by_type,
        "by_level": by_level,
        "by_status": by_status,
        "occurred_count": sum(1 for r in risks if r.is_occurred),
        "closed_count": sum(1 for r in risks if r.status == RiskStatusEnum.CLOSED),
        "high_priority_count": high_priority_count,
        "avg_risk_score": round(avg_score, 2),
    }
    
    return ResponseModel(
        code=200,
        message="获取风险汇总统计成功",
        data=summary
    )
