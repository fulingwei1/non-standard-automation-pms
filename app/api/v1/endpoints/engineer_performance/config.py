# -*- coding: utf-8 -*-
"""
配置管理端点
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.engineer_performance import (
    DimensionConfigCreate,
    DimensionConfigUpdate,
)
from app.services.engineer_performance.engineer_performance_service import (
    EngineerPerformanceService,
)

router = APIRouter(prefix="/config", tags=["配置管理"])


@router.get("/weights", summary="获取权重配置列表")
async def list_dimension_configs(
    job_type: Optional[str] = Query(None, description="岗位类型"),
    include_expired: bool = Query(False, description="是否包含已过期配置"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取五维权重配置列表"""
    service = EngineerPerformanceService(db)

    configs = service.list_dimension_configs(
        job_type=job_type,
        include_expired=include_expired
    )

    items = []
    for c in configs:
        # 统计受影响人数
        affected_count = service.count_engineers_by_config(c.job_type, c.job_level)
        items.append({
            "id": c.id,
            "job_type": c.job_type,
            "job_level": c.job_level,
            "config_name": c.config_name,
            "technical_weight": c.technical_weight,
            "execution_weight": c.execution_weight,
            "cost_quality_weight": c.cost_quality_weight,
            "knowledge_weight": c.knowledge_weight,
            "collaboration_weight": c.collaboration_weight,
            "effective_date": c.effective_date.isoformat() if c.effective_date else None,
            "expired_date": c.expired_date.isoformat() if c.expired_date else None,
            "affected_count": affected_count,
            "description": c.description
        })

    return ResponseModel(
        code=200,
        message="success",
        data=items
    )


@router.get("/weights/{job_type}", summary="获取指定岗位权重配置")
async def get_dimension_config(
    job_type: str,
    job_level: Optional[str] = Query(None, description="职级"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定岗位类型的权重配置"""
    if job_type not in ['mechanical', 'test', 'electrical']:
        raise HTTPException(status_code=400, detail="无效的岗位类型")

    service = EngineerPerformanceService(db)
    config = service.get_dimension_config(job_type, job_level)

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    affected_count = service.count_engineers_by_config(config.job_type, config.job_level)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": config.id,
            "job_type": config.job_type,
            "job_level": config.job_level,
            "config_name": config.config_name,
            "technical_weight": config.technical_weight,
            "execution_weight": config.execution_weight,
            "cost_quality_weight": config.cost_quality_weight,
            "knowledge_weight": config.knowledge_weight,
            "collaboration_weight": config.collaboration_weight,
            "effective_date": config.effective_date.isoformat() if config.effective_date else None,
            "affected_count": affected_count,
            "description": config.description
        }
    )


@router.post("/weights", summary="创建权重配置")
async def create_dimension_config(
    data: DimensionConfigCreate,
    require_approval: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的五维权重配置

    支持：
    - 全局配置（需要管理员权限）
    - 部门级别配置（部门经理可以为部门创建，需要审批）
    """
    if data.job_type not in ['mechanical', 'test', 'electrical', 'solution']:
        raise HTTPException(status_code=400, detail="无效的岗位类型")

    service = EngineerPerformanceService(db)

    try:
        # 如果是全局配置，需要管理员权限
        if not data.department_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="只有管理员可以创建全局配置")

        config = service.create_dimension_config(
            data,
            current_user.id,
            department_id=data.department_id,
            require_approval=require_approval
        )

        # 统计受影响人数
        affected_count = service.count_engineers_by_config(
            config.job_type,
            config.job_level,
            department_id=config.department_id
        )

        return ResponseModel(
            code=200,
            message="配置创建成功" + ("（待审批）" if config.approval_status == 'PENDING' else ""),
            data={
                "id": config.id,
                "affected_count": affected_count,
                "approval_status": config.approval_status,
                "is_global": config.is_global
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/grades", summary="获取等级规则")
async def get_grade_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取绩效等级划分规则"""
    return ResponseModel(
        code=200,
        message="success",
        data={
            "grades": [
                {"grade": "S", "name": "优秀", "min_score": 85, "max_score": 100, "color": "#52c41a"},
                {"grade": "A", "name": "良好", "min_score": 70, "max_score": 84, "color": "#1890ff"},
                {"grade": "B", "name": "合格", "min_score": 60, "max_score": 69, "color": "#faad14"},
                {"grade": "C", "name": "待改进", "min_score": 40, "max_score": 59, "color": "#fa8c16"},
                {"grade": "D", "name": "不合格", "min_score": 0, "max_score": 39, "color": "#f5222d"},
            ]
        }
    )


@router.get("/job-types", summary="获取岗位类型列表")
async def get_job_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取支持的岗位类型列表"""
    service = EngineerPerformanceService(db)

    job_types = []
    for job_type, label in [
        ('mechanical', '机械工程师'),
        ('test', '测试工程师'),
        ('electrical', '电气工程师')
    ]:
        count = service.count_engineers_by_config(job_type, None)
        job_types.append({
            "value": job_type,
            "label": label,
            "count": count
        })

    return ResponseModel(
        code=200,
        message="success",
        data=job_types
    )


@router.get("/job-levels", summary="获取职级列表")
async def get_job_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取支持的职级列表"""
    return ResponseModel(
        code=200,
        message="success",
        data=[
            {"value": "junior", "label": "初级"},
            {"value": "intermediate", "label": "中级"},
            {"value": "senior", "label": "高级"},
            {"value": "expert", "label": "资深/专家"},
        ]
    )


@router.get("/department-configs", summary="获取部门评价指标配置")
async def get_department_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """部门经理获取管理的部门的评价指标配置"""
    service = EngineerPerformanceService(db)

    try:
        configs = service.get_department_configs(current_user.id)
        return ResponseModel(
            code=200,
            message="获取部门配置成功",
            data=configs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/department-configs", summary="创建部门级别权重配置")
async def create_department_config(
    data: DimensionConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    部门经理为部门创建评价指标配置

    注意：
    - 只有部门经理可以为自己的部门创建配置
    - 部门级别配置需要审批后才能生效
    """
    if not data.department_id:
        raise HTTPException(status_code=400, detail="部门级别配置必须指定部门ID")

    service = EngineerPerformanceService(db)

    try:
        config = service.create_dimension_config(
            data,
            current_user.id,
            department_id=data.department_id,
            require_approval=True  # 部门级别配置需要审批
        )

        return ResponseModel(
            code=200,
            message="部门配置创建成功，等待审批",
            data={
                "id": config.id,
                "approval_status": config.approval_status,
                "department_id": config.department_id
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-approvals", summary="获取待审批配置列表")
async def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待审批的部门级别配置（管理员功能）"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以查看待审批配置")

    service = EngineerPerformanceService(db)
    pending = service.get_pending_approvals()

    items = []
    for config in pending:
        from app.models.organization import Department
        dept = db.query(Department).filter(Department.id == config.department_id).first()

        items.append({
            "id": config.id,
            "job_type": config.job_type,
            "job_level": config.job_level,
            "department_id": config.department_id,
            "department_name": dept.dept_name if dept else None,
            "technical_weight": config.technical_weight,
            "execution_weight": config.execution_weight,
            "cost_quality_weight": config.cost_quality_weight,
            "knowledge_weight": config.knowledge_weight,
            "collaboration_weight": config.collaboration_weight,
            "config_name": config.config_name,
            "description": config.description,
            "effective_date": config.effective_date.isoformat() if config.effective_date else None,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "operator_id": config.operator_id
        })

    return ResponseModel(
        code=200,
        message="获取待审批配置成功",
        data=items
    )


class ApproveConfigRequest(BaseModel):
    """审批配置请求"""
    approved: bool = Field(..., description="是否批准")
    approval_reason: Optional[str] = Field(None, description="审批理由")


@router.post("/approve/{config_id}", summary="审批部门级别配置")
async def approve_dimension_config(
    config_id: int,
    request: ApproveConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审批部门级别配置（管理员功能）"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以审批配置")

    service = EngineerPerformanceService(db)

    try:
        config = service.approve_dimension_config(
            config_id=config_id,
            approver_id=current_user.id,
            approved=request.approved,
            approval_reason=request.approval_reason
        )

        return ResponseModel(
            code=200,
            message="审批" + ("通过" if request.approved else "拒绝"),
            data={
                "id": config.id,
                "approval_status": config.approval_status
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
