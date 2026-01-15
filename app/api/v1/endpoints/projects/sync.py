# -*- coding: utf-8 -*-
"""
项目数据同步端点

包含：合同数据同步、ERP系统集成等
"""

from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.schemas.common import ResponseModel

from .utils import _sync_to_erp_system

router = APIRouter()


# ==================== 合同数据同步 ====================

@router.post("/{project_id}/sync-from-contract", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_project_from_contract(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    contract_id: Optional[int] = Query(None, description="��同ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从合同同步数据到项目
    """
    from app.services.data_sync_service import DataSyncService
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    sync_service = DataSyncService(db)

    if contract_id:
        result = sync_service.sync_contract_to_project(contract_id)
    else:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        from app.models.sales import Contract
        contracts = db.query(Contract).filter(Contract.project_id == project_id).all()

        if not contracts:
            return ResponseModel(
                code=200,
                message="项目未关联合同，无需同步",
                data={"synced_contracts": []}
            )

        synced_contracts = []
        for contract in contracts:
            result = sync_service.sync_contract_to_project(contract.id)
            if result.get("success"):
                synced_contracts.append({
                    "contract_id": contract.id,
                    "contract_code": contract.contract_code,
                    "updated_fields": result.get("updated_fields", [])
                })

        return ResponseModel(
            code=200,
            message=f"已同步 {len(synced_contracts)} 个合同",
            data={"synced_contracts": synced_contracts}
        )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "同步失败"))

    return ResponseModel(
        code=200,
        message=result.get("message", "同步成功"),
        data=result
    )


@router.post("/{project_id}/sync-to-contract", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_project_to_contract(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    同步项目数据到合同
    """
    from app.services.data_sync_service import DataSyncService
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    sync_service = DataSyncService(db)
    result = sync_service.sync_project_to_contract(project_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "同步失败"))

    return ResponseModel(
        code=200,
        message=result.get("message", "同步成功"),
        data=result
    )


@router.get("/{project_id}/sync-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_sync_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目数据同步状态
    """
    from app.services.data_sync_service import DataSyncService
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    sync_service = DataSyncService(db)
    result = sync_service.get_sync_status(project_id=project_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "查询失败"))

    return ResponseModel(
        code=200,
        message="获取同步状态成功",
        data=result
    )


# ==================== ERP集成 ====================

@router.post("/{project_id}/sync-to-erp", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_project_to_erp(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    erp_order_no: Optional[str] = Body(None, description="ERP订单号"),
    current_user: User = Depends(security.require_permission("project:erp:sync")),
) -> Any:
    """
    同步项目到ERP系统
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    sync_result = _sync_to_erp_system(project, erp_order_no)

    if sync_result['success']:
        project.erp_synced = True
        project.erp_sync_time = datetime.now()
        project.erp_sync_status = "SYNCED"
    else:
        project.erp_sync_status = "FAILED"
        project.erp_error_message = sync_result.get('error', '同步失败')
        db.commit()
        raise HTTPException(status_code=500, detail=f"ERP同步失败: {sync_result.get('error')}")

    if erp_order_no:
        project.erp_order_no = erp_order_no
    elif not project.erp_order_no:
        project.erp_order_no = f"ERP-{project.project_code}"

    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="项目已同步到ERP系统",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "erp_order_no": project.erp_order_no,
            "erp_sync_time": project.erp_sync_time.isoformat() if project.erp_sync_time else None,
            "erp_sync_status": project.erp_sync_status
        }
    )


@router.get("/{project_id}/erp-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_erp_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目ERP同步状态
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    return ResponseModel(
        code=200,
        message="获取ERP状态成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "erp_synced": project.erp_synced,
            "erp_sync_time": project.erp_sync_time.isoformat() if project.erp_sync_time else None,
            "erp_order_no": project.erp_order_no,
            "erp_sync_status": project.erp_sync_status
        }
    )


@router.put("/{project_id}/erp-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_erp_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    erp_synced: Optional[bool] = Body(None, description="是否已录入ERP系统"),
    erp_order_no: Optional[str] = Body(None, description="ERP订单号"),
    erp_sync_status: Optional[str] = Body(None, description="ERP同步状态"),
    current_user: User = Depends(security.require_permission("project:erp:update")),
) -> Any:
    """
    更新项目ERP同步状态
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if erp_synced is not None:
        project.erp_synced = erp_synced
        if erp_synced and not project.erp_sync_time:
            project.erp_sync_time = datetime.now()

    if erp_order_no is not None:
        project.erp_order_no = erp_order_no

    if erp_sync_status is not None:
        if erp_sync_status not in ["PENDING", "SYNCED", "FAILED"]:
            raise HTTPException(status_code=400, detail="无效的ERP同步状态")
        project.erp_sync_status = erp_sync_status

    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="ERP状态更新成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "erp_synced": project.erp_synced,
            "erp_sync_time": project.erp_sync_time.isoformat() if project.erp_sync_time else None,
            "erp_order_no": project.erp_order_no,
            "erp_sync_status": project.erp_sync_status
        }
    )
