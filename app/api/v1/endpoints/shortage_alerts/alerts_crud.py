# -*- coding: utf-8 -*-
"""
预警CRUD - 自动生成
从 shortage_alerts.py 拆分
"""

from typing import Any, List, Optional

from datetime import date, datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from sqlalchemy.orm import Session

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.material import MaterialShortage, Material, BomItem

from app.models.project import Project, Machine

from app.models.shortage import (
    ShortageReport,
    MaterialArrival,
    ArrivalFollowUp,
    MaterialSubstitution,
    MaterialTransfer,
)
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.production import WorkOrder
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.shortage import (
    ShortageReportCreate,
    ShortageReportResponse,
    ShortageReportListResponse,
    MaterialArrivalResponse,
    MaterialArrivalListResponse,
    ArrivalFollowUpCreate,
    MaterialSubstitutionCreate,
    MaterialSubstitutionResponse,
    MaterialSubstitutionListResponse,
    MaterialTransferCreate,
    MaterialTransferResponse,
    MaterialTransferListResponse,
)

router = APIRouter(tags=["alerts_crud"])

# 共 12 个路由

@router.get("/", response_model=PaginatedResponse)
def read_shortage_alerts(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    material_id: Optional[int] = Query(None, description="物料ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    alert_level: Optional[str] = Query(None, description="预警级别筛选"),
    handler_id: Optional[int] = Query(None, description="处理人ID筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    获取缺料预警列表（支持分页、筛选）
    """
    query = db.query(MaterialShortage)
    
    # 项目筛选
    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)
    
    # 物料筛选
    if material_id:
        query = query.filter(MaterialShortage.material_id == material_id)
    
    # 状态筛选
    if status:
        query = query.filter(MaterialShortage.status == status)
    
    # 预警级别筛选
    if alert_level:
        query = query.filter(MaterialShortage.alert_level == alert_level)
    
    # 处理人筛选
    if handler_id:
        query = query.filter(MaterialShortage.handler_id == handler_id)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    alerts = query.order_by(desc(MaterialShortage.created_at)).offset(offset).limit(page_size).all()
    
    # 构建响应数据
    items = []
    for alert in alerts:
        items.append({
            "id": alert.id,
            "project_id": alert.project_id,
            "project_name": alert.project.project_name if alert.project else None,
            "material_id": alert.material_id,
            "material_code": alert.material_code,
            "material_name": alert.material_name,
            "required_qty": float(alert.required_qty),
            "available_qty": float(alert.available_qty),
            "shortage_qty": float(alert.shortage_qty),
            "required_date": alert.required_date.isoformat() if alert.required_date else None,
            "status": alert.status,
            "alert_level": alert.alert_level,
            "handler_id": alert.handler_id,
            "solution": alert.solution,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        })
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{alert_id}")
def get_shortage_alert_detail(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    获取缺料预警详情
    """
    alert = db.query(MaterialShortage).filter(MaterialShortage.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="缺料预警不存在")
    
    return {
        "id": alert.id,
        "project_id": alert.project_id,
        "project_name": alert.project.project_name if alert.project else None,
        "bom_item_id": alert.bom_item_id,
        "material_id": alert.material_id,
        "material_code": alert.material_code,
        "material_name": alert.material_name,
        "required_qty": float(alert.required_qty),
        "available_qty": float(alert.available_qty),
        "shortage_qty": float(alert.shortage_qty),
        "required_date": alert.required_date.isoformat() if alert.required_date else None,
        "status": alert.status,
        "alert_level": alert.alert_level,
        "handler_id": alert.handler_id,
        "solution": alert.solution,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "remark": alert.remark,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
    }


@router.put("/{alert_id}/acknowledge", response_model=ResponseModel)
def acknowledge_shortage_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    确认缺料预警（PMC确认）
    """
    alert = db.query(MaterialShortage).filter(MaterialShortage.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="缺料预警不存在")
    
    if alert.status != "OPEN":
        raise HTTPException(status_code=400, detail="只有OPEN状态的预警才能确认")
    
    # 更新状态为已确认（可以自定义状态值，这里使用ACKNOWLEDGED）
    alert.status = "ACKNOWLEDGED"
    alert.handler_id = current_user.id
    
    db.add(alert)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="预警已确认"
    )


@router.patch("/{alert_id}", response_model=ResponseModel)
def update_shortage_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    solution: Optional[str] = Body(None, description="解决方案"),
    handler_id: Optional[int] = Body(None, description="处理人ID"),
    alert_level: Optional[str] = Body(None, description="预警级别"),
    remark: Optional[str] = Body(None, description="备注"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    更新缺料预警（处理预警）
    """
    alert = db.query(MaterialShortage).filter(MaterialShortage.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="缺料预警不存在")
    
    if solution is not None:
        alert.solution = solution
    
    if handler_id is not None:
        # 检查处理人是否存在
        handler = db.query(User).filter(User.id == handler_id).first()
        if not handler:
            raise HTTPException(status_code=404, detail="处理人不存在")
        alert.handler_id = handler_id
    
    if alert_level is not None:
        if alert_level not in ["LOW", "WARNING", "HIGH", "CRITICAL"]:
            raise HTTPException(status_code=400, detail="无效的预警级别")
        alert.alert_level = alert_level
    
    if remark is not None:
        alert.remark = remark
    
    # 缺料联动：如果预警级别提升到level3/level4，自动阻塞相关任务
    old_alert_level = alert.alert_level
    new_alert_level = alert_level if alert_level else alert.alert_level
    
    db.add(alert)
    db.flush()
    
    # 缺料联动：如果预警级别提升或影响类型变为stop/delivery，触发任务阻塞
    try:
        from app.models.shortage import ShortageAlert as ShortageAlertModel
        from app.services.progress_integration_service import ProgressIntegrationService
        
        # 查找对应的ShortageAlert记录（如果存在）
        shortage_alert = db.query(ShortageAlertModel).filter(
            ShortageAlertModel.project_id == alert.project_id,
            ShortageAlertModel.material_code == alert.material_code,
            ShortageAlertModel.status.in_(['pending', 'handling'])
        ).first()
        
        if shortage_alert:
            # 如果预警级别提升到CRITICAL/HIGH，触发任务阻塞
            critical_levels = ['CRITICAL', 'HIGH', 'level3', 'level4', 'L3', 'L4']
            if (new_alert_level in critical_levels and 
                old_alert_level not in critical_levels):
                integration_service = ProgressIntegrationService(db)
                blocked_tasks = integration_service.handle_shortage_alert_created(shortage_alert)
                if blocked_tasks:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"缺料预警级别提升，已阻塞 {len(blocked_tasks)} 个任务")
    except Exception as e:
        # 联动失败不影响预警更新，记录日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"缺料联动处理失败: {str(e)}", exc_info=True)
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message="预警已更新"
    )


@router.post("/{alert_id}/follow-ups", response_model=ResponseModel)
def add_shortage_alert_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    follow_up_note: str = Body(..., description="跟进内容"),
    follow_up_type: Optional[str] = Body("COMMENT", description="跟进类型：COMMENT/CALL/EMAIL/VISIT"),
    next_follow_up_date: Optional[date] = Body(None, description="下次跟进日期"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    添加缺料预警跟进记录
    """
    alert = db.query(MaterialShortage).filter(MaterialShortage.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="缺料预警不存在")
    
    # 将跟进记录存储到备注字段（简化实现，实际应该创建专门的跟进记录表）
    # 格式：JSON数组存储跟进记录
    import json
    follow_ups = []
    
    # 尝试从备注中解析已有的跟进记录
    if alert.remark:
        try:
            # 检查备注是否是JSON格式的跟进记录
            parsed = json.loads(alert.remark)
            if isinstance(parsed, list):
                follow_ups = parsed
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON，保留原备注作为第一条记录
            if alert.remark.strip():
                follow_ups.append({
                    "type": "NOTE",
                    "note": alert.remark,
                    "created_at": alert.created_at.isoformat() if alert.created_at else datetime.now().isoformat(),
                    "created_by": alert.handler_id,
                })
    
    # 添加新的跟进记录
    follow_ups.append({
        "type": follow_up_type or "COMMENT",
        "note": follow_up_note,
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.id,
        "created_by_name": current_user.real_name or current_user.username,
        "next_follow_up_date": next_follow_up_date.isoformat() if next_follow_up_date else None,
    })
    
    # 更新备注字段
    alert.remark = json.dumps(follow_ups, ensure_ascii=False)
    
    db.add(alert)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="跟进记录已添加",
        data={
            "alert_id": alert_id,
            "follow_up_count": len(follow_ups),
            "latest_follow_up": follow_ups[-1] if follow_ups else None,
        }
    )


@router.get("/{alert_id}/follow-ups", response_model=ResponseModel)
def get_shortage_alert_follow_ups(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    获取缺料预警的跟进记录列表
    """
    alert = db.query(MaterialShortage).filter(MaterialShortage.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="缺料预警不存在")
    
    import json
    follow_ups = []
    
    # 尝试从备注中解析跟进记录
    if alert.remark:
        try:
            parsed = json.loads(alert.remark)
            if isinstance(parsed, list):
                follow_ups = parsed
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON，返回原备注作为单条记录
            if alert.remark.strip():
                follow_ups.append({
                    "type": "NOTE",
                    "note": alert.remark,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                    "created_by": alert.handler_id,
                })
    
    return ResponseModel(
        code=200,
        message="获取跟进记录成功",
        data={
            "alert_id": alert_id,
            "follow_ups": follow_ups,
            "total_count": len(follow_ups),
        }
    )


@router.post("/{alert_id}/resolve", response_model=ResponseModel)
def resolve_shortage_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    solution: Optional[str] = Body(None, description="解决方案"),
    current_user: User = Depends(security.require_permission("shortage_alert:resolve")),
) -> Any:
    """
    解决缺料预警（结案）
    """
    alert = db.query(MaterialShortage).filter(MaterialShortage.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="缺料预警不存在")
    
    if alert.status == "RESOLVED":
        raise HTTPException(status_code=400, detail="预警已解决")
    
    old_status = alert.status
    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now()
    alert.handler_id = current_user.id
    
    if solution:
        alert.solution = solution
    
    db.add(alert)
    db.flush()
    
    # 缺料联动：解决缺料预警，自动解除相关任务阻塞
    try:
        from app.models.shortage import ShortageAlert as ShortageAlertModel
        from app.services.progress_integration_service import ProgressIntegrationService
        
        # 查找对应的ShortageAlert记录（如果存在）
        shortage_alert = db.query(ShortageAlertModel).filter(
            ShortageAlertModel.project_id == alert.project_id,
            ShortageAlertModel.material_code == alert.material_code,
            ShortageAlertModel.status.in_(['pending', 'handling'])
        ).first()
        
        if shortage_alert:
            integration_service = ProgressIntegrationService(db)
            unblocked_tasks = integration_service.handle_shortage_alert_resolved(shortage_alert)
            if unblocked_tasks:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"缺料预警解决，已解除 {len(unblocked_tasks)} 个任务阻塞")
    except Exception as e:
        # 联动失败不影响缺料预警解决，记录日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"缺料联动处理失败: {str(e)}", exc_info=True)
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message="预警已解决"
    )

