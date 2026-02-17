# -*- coding: utf-8 -*-
"""
预警管理 - alerts.py

合并来源:
- app/api/v1/endpoints/shortage_alerts/alerts_crud.py

路由:
- GET    /alerts                    预警列表（系统检测）
- GET    /alerts/{id}               预警详情
- PUT    /alerts/{id}/acknowledge   确认预警
- PATCH  /alerts/{id}               更新预警
- POST   /alerts/{id}/resolve       解决预警
- POST   /alerts/{id}/follow-ups    添加跟进
- GET    /alerts/{id}/follow-ups    跟进列表
"""
import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.material import MaterialShortage
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 辅助函数
# ============================================================

def _build_alert_response(alert: MaterialShortage) -> Dict[str, Any]:
    """构建预警响应对象"""
    return {
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
    }


def _build_alert_detail_response(alert: MaterialShortage) -> Dict[str, Any]:
    """构建预警详情响应对象"""
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


def _parse_follow_ups(remark: Optional[str], created_at: Optional[datetime], handler_id: Optional[int]) -> List[Dict]:
    """从备注字段解析跟进记录"""
    follow_ups = []
    if not remark:
        return follow_ups

    try:
        parsed = json.loads(remark)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        # 如果不是JSON，返回原备注作为单条记录
        if remark.strip():
            follow_ups.append({
                "type": "NOTE",
                "note": remark,
                "created_at": created_at.isoformat() if created_at else None,
                "created_by": handler_id,
            })
    return follow_ups


def _handle_shortage_integration(
    db: Session,
    alert: MaterialShortage,
    action: str,
    old_level: Optional[str] = None,
    new_level: Optional[str] = None
) -> None:
    """处理缺料联动（任务阻塞/解除）"""
    try:
        from app.models.alert import AlertRecord
        from app.services.progress_integration_service import ProgressIntegrationService

        # 查找对应的 AlertRecord 记录
        shortage_alert = db.query(AlertRecord).filter(
            AlertRecord.target_type == 'SHORTAGE',
            AlertRecord.project_id == alert.project_id,
            AlertRecord.target_no == alert.material_code,
            AlertRecord.status.in_(['PENDING', 'PROCESSING', 'pending', 'handling'])
        ).first()

        if not shortage_alert:
            return

        integration_service = ProgressIntegrationService(db)
        critical_levels = ['CRITICAL', 'HIGH', 'level3', 'level4', 'L3', 'L4']

        if action == "level_upgrade":
            # 预警级别提升，触发任务阻塞
            if new_level in critical_levels and old_level not in critical_levels:
                blocked_tasks = integration_service.handle_shortage_alert_created(shortage_alert)
                if blocked_tasks:
                    logger.info(f"缺料预警级别提升，已阻塞 {len(blocked_tasks)} 个任务")

        elif action == "resolved":
            # 预警解决，解除任务阻塞
            unblocked_tasks = integration_service.handle_shortage_alert_resolved(shortage_alert)
            if unblocked_tasks:
                logger.info(f"缺料预警解决，已解除 {len(unblocked_tasks)} 个任务阻塞")

    except Exception as e:
        logger.error(f"缺料联动处理失败: {str(e)}", exc_info=True)


# ============================================================
# 预警列表和详情
# ============================================================

@router.get("/alerts", response_model=PaginatedResponse)
def list_alerts(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    material_id: Optional[int] = Query(None, description="物料ID筛选"),
    alert_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    alert_level: Optional[str] = Query(None, description="预警级别筛选"),
    handler_id: Optional[int] = Query(None, description="处理人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取缺料预警列表（系统检测的缺料）
    """
    query = db.query(MaterialShortage)

    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)
    if material_id:
        query = query.filter(MaterialShortage.material_id == material_id)
    if alert_status:
        query = query.filter(MaterialShortage.status == alert_status)
    if alert_level:
        query = query.filter(MaterialShortage.alert_level == alert_level)
    if handler_id:
        query = query.filter(MaterialShortage.handler_id == handler_id)

    total = query.count()
    alerts = apply_pagination(query.order_by(desc(MaterialShortage.created_at)), pagination.offset, pagination.limit).all()

    items = [_build_alert_response(alert) for alert in alerts]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/alerts/{alert_id}", response_model=ResponseModel)
def get_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取缺料预警详情
    """
    alert = get_or_404(db, MaterialShortage, alert_id, "缺料预警不存在")

    return ResponseModel(code=200, message="success", data=_build_alert_detail_response(alert))


# ============================================================
# 预警处理
# ============================================================

@router.put("/alerts/{alert_id}/acknowledge", response_model=ResponseModel)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认缺料预警（PMC确认）
    """
    alert = get_or_404(db, MaterialShortage, alert_id, "缺料预警不存在")

    if alert.status != "OPEN":
        raise HTTPException(status_code=400, detail="只有OPEN状态的预警才能确认")

    alert.status = "ACKNOWLEDGED"
    alert.handler_id = current_user.id

    db.add(alert)
    db.commit()

    return ResponseModel(code=200, message="预警已确认")


@router.patch("/alerts/{alert_id}", response_model=ResponseModel)
def update_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    solution: Optional[str] = Body(None, description="解决方案"),
    handler_id: Optional[int] = Body(None, description="处理人ID"),
    alert_level: Optional[str] = Body(None, description="预警级别"),
    remark: Optional[str] = Body(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新缺料预警
    """
    alert = get_or_404(db, MaterialShortage, alert_id, "缺料预警不存在")

    old_alert_level = alert.alert_level

    if solution is not None:
        alert.solution = solution

    if handler_id is not None:
        handler = get_or_404(db, User, handler_id, "处理人不存在")
        alert.handler_id = handler_id

    if alert_level is not None:
        if alert_level not in ["LOW", "WARNING", "HIGH", "CRITICAL"]:
            raise HTTPException(status_code=400, detail="无效的预警级别")
        alert.alert_level = alert_level

    if remark is not None:
        alert.remark = remark

    db.add(alert)
    db.flush()

    # 缺料联动：如果预警级别提升，触发任务阻塞
    new_alert_level = alert_level if alert_level else alert.alert_level
    _handle_shortage_integration(db, alert, "level_upgrade", old_alert_level, new_alert_level)

    db.commit()

    return ResponseModel(code=200, message="预警已更新")


@router.post("/alerts/{alert_id}/resolve", response_model=ResponseModel)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    solution: Optional[str] = Body(None, description="解决方案"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    解决缺料预警（结案）
    """
    alert = get_or_404(db, MaterialShortage, alert_id, "缺料预警不存在")

    if alert.status == "RESOLVED":
        raise HTTPException(status_code=400, detail="预警已解决")

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now()
    alert.handler_id = current_user.id

    if solution:
        alert.solution = solution

    db.add(alert)
    db.flush()

    # 缺料联动：解决预警，解除任务阻塞
    _handle_shortage_integration(db, alert, "resolved")

    db.commit()

    return ResponseModel(code=200, message="预警已解决")


# ============================================================
# 跟进管理
# ============================================================

@router.post("/alerts/{alert_id}/follow-ups", response_model=ResponseModel)
def add_follow_up(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    follow_up_note: str = Body(..., description="跟进内容"),
    follow_up_type: Optional[str] = Body("COMMENT", description="跟进类型：COMMENT/CALL/EMAIL/VISIT"),
    next_follow_up_date: Optional[date] = Body(None, description="下次跟进日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加缺料预警跟进记录
    """
    alert = get_or_404(db, MaterialShortage, alert_id, "缺料预警不存在")

    # 解析现有跟进记录
    follow_ups = _parse_follow_ups(alert.remark, alert.created_at, alert.handler_id)

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


@router.get("/alerts/{alert_id}/follow-ups", response_model=ResponseModel)
def list_follow_ups(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取缺料预警的跟进记录列表
    """
    alert = get_or_404(db, MaterialShortage, alert_id, "缺料预警不存在")

    follow_ups = _parse_follow_ups(alert.remark, alert.created_at, alert.handler_id)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "alert_id": alert_id,
            "follow_ups": follow_ups,
            "total_count": len(follow_ups),
        }
    )
