# -*- coding: utf-8 -*-
"""
缺料预警管理 API endpoints
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
    ShortageReport, MaterialArrival, ArrivalFollowUp,
    MaterialSubstitution, MaterialTransfer
)
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.production import WorkOrder
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.shortage import (
    ShortageReportCreate, ShortageReportResponse, ShortageReportListResponse,
    MaterialArrivalResponse, MaterialArrivalListResponse, ArrivalFollowUpCreate,
    MaterialSubstitutionCreate, MaterialSubstitutionResponse, MaterialSubstitutionListResponse,
    MaterialTransferCreate, MaterialTransferResponse, MaterialTransferListResponse
)

router = APIRouter()


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
        except:
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
        except:
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


@router.get("/statistics/overview")
def get_shortage_alerts_statistics(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    获取缺料预警统计（按级别/类型）
    """
    query = db.query(MaterialShortage)
    
    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)
    
    # 按状态统计
    status_stats = {}
    status_counts = (
        db.query(MaterialShortage.status, func.count(MaterialShortage.id))
        .filter(MaterialShortage.project_id == project_id if project_id else True)
        .group_by(MaterialShortage.status)
        .all()
    )
    for status, count in status_counts:
        status_stats[status] = count
    
    # 按预警级别统计
    level_stats = {}
    level_counts = (
        db.query(MaterialShortage.alert_level, func.count(MaterialShortage.id))
        .filter(MaterialShortage.project_id == project_id if project_id else True)
        .group_by(MaterialShortage.alert_level)
        .all()
    )
    for level, count in level_counts:
        level_stats[level] = count
    
    # 总数
    total = query.count()
    
    # 未解决数量
    unresolved = query.filter(MaterialShortage.status != "RESOLVED").count()
    
    return {
        "total": total,
        "unresolved": unresolved,
        "resolved": total - unresolved,
        "by_status": status_stats,
        "by_level": level_stats,
    }


@router.get("/dashboard")
def get_shortage_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料看板
    """
    query = db.query(MaterialShortage)
    
    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)
    
    # 获取所有缺料预警
    alerts = query.filter(MaterialShortage.status != "RESOLVED").all()
    
    # 按项目分组统计
    project_stats = {}
    for alert in alerts:
        if alert.project_id not in project_stats:
            project = db.query(Project).filter(Project.id == alert.project_id).first()
            project_stats[alert.project_id] = {
                "project_id": alert.project_id,
                "project_name": project.project_name if project else None,
                "total_shortages": 0,
                "critical_shortages": 0,
                "high_shortages": 0,
                "warning_shortages": 0,
                "total_shortage_qty": Decimal("0"),
                "materials": []
            }
        
        stats = project_stats[alert.project_id]
        stats["total_shortages"] += 1
        stats["total_shortage_qty"] += alert.shortage_qty or Decimal("0")
        
        if alert.alert_level == "CRITICAL":
            stats["critical_shortages"] += 1
        elif alert.alert_level == "HIGH":
            stats["high_shortages"] += 1
        else:
            stats["warning_shortages"] += 1
        
        # 添加物料信息
        stats["materials"].append({
            "material_id": alert.material_id,
            "material_code": alert.material_code,
            "material_name": alert.material_name,
            "shortage_qty": float(alert.shortage_qty),
            "required_date": alert.required_date.isoformat() if alert.required_date else None,
            "alert_level": alert.alert_level,
            "status": alert.status
        })
    
    # 转换为列表
    project_list = []
    for project_id, stats in project_stats.items():
        project_list.append({
            **stats,
            "total_shortage_qty": float(stats["total_shortage_qty"])
        })
    
    # 全局统计
    total_projects = len(project_list)
    total_shortages = len(alerts)
    critical_count = len([a for a in alerts if a.alert_level == "CRITICAL"])
    high_count = len([a for a in alerts if a.alert_level == "HIGH"])
    warning_count = len([a for a in alerts if a.alert_level == "WARNING"])
    
    return {
        "summary": {
            "total_projects": total_projects,
            "total_shortages": total_shortages,
            "critical_count": critical_count,
            "high_count": high_count,
            "warning_count": warning_count
        },
        "projects": project_list
    }


@router.get("/supplier-delivery")
def get_supplier_delivery_analysis(
    *,
    db: Session = Depends(deps.get_db),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    供应商交期分析
    """
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem
    from app.models.material import Supplier
    
    query = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED", "RECEIVED"]))
    
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    
    if start_date:
        query = query.filter(PurchaseOrder.order_date >= start_date)
    
    if end_date:
        query = query.filter(PurchaseOrder.order_date <= end_date)
    
    orders = query.all()
    
    supplier_stats = {}
    for order in orders:
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        supplier_name = supplier.supplier_name if supplier else None
        
        if order.supplier_id not in supplier_stats:
            supplier_stats[order.supplier_id] = {
                "supplier_id": order.supplier_id,
                "supplier_name": supplier_name,
                "total_orders": 0,
                "on_time_orders": 0,
                "delayed_orders": 0,
                "total_items": 0,
                "on_time_items": 0,
                "delayed_items": 0,
                "avg_delay_days": 0
            }
        
        stats = supplier_stats[order.supplier_id]
        stats["total_orders"] += 1
        
        # 检查订单是否延迟
        if order.required_date and order.actual_receipt_date:
            if order.actual_receipt_date > order.required_date:
                stats["delayed_orders"] += 1
                delay_days = (order.actual_receipt_date - order.required_date).days
                stats["avg_delay_days"] = (stats["avg_delay_days"] * (stats["delayed_orders"] - 1) + delay_days) / stats["delayed_orders"]
            else:
                stats["on_time_orders"] += 1
        
        # 统计订单明细
        items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.order_id == order.id).all()
        for item in items:
            stats["total_items"] += 1
            if item.required_date and item.received_date:
                if item.received_date <= item.required_date:
                    stats["on_time_items"] += 1
                else:
                    stats["delayed_items"] += 1
    
    # 转换为列表
    supplier_list = []
    for supplier_id, stats in supplier_stats.items():
        on_time_rate = (stats["on_time_orders"] / stats["total_orders"] * 100) if stats["total_orders"] > 0 else 0
        supplier_list.append({
            **stats,
            "on_time_rate": round(on_time_rate, 2)
        })
    
    return {
        "suppliers": supplier_list,
        "total_suppliers": len(supplier_list)
    }


@router.get("/daily-report")
def get_shortage_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    report_date: Optional[date] = Query(None, description="报告日期（默认今天）"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料日报
    """
    if not report_date:
        report_date = datetime.now().date()
    
    # 获取当天的缺料预警
    alerts = db.query(MaterialShortage).filter(
        func.date(MaterialShortage.created_at) == report_date
    ).all()
    
    # 按项目统计
    project_stats = {}
    for alert in alerts:
        if alert.project_id not in project_stats:
            project = db.query(Project).filter(Project.id == alert.project_id).first()
            project_stats[alert.project_id] = {
                "project_id": alert.project_id,
                "project_name": project.project_name if project else None,
                "shortage_count": 0,
                "total_shortage_qty": Decimal("0"),
                "critical_count": 0,
                "materials": []
            }
        
        stats = project_stats[alert.project_id]
        stats["shortage_count"] += 1
        stats["total_shortage_qty"] += alert.shortage_qty or Decimal("0")
        
        if alert.alert_level == "CRITICAL":
            stats["critical_count"] += 1
        
        stats["materials"].append({
            "material_code": alert.material_code,
            "material_name": alert.material_name,
            "shortage_qty": float(alert.shortage_qty),
            "alert_level": alert.alert_level
        })
    
    # 转换为列表
    project_list = []
    for project_id, stats in project_stats.items():
        project_list.append({
            **stats,
            "total_shortage_qty": float(stats["total_shortage_qty"])
        })
    
    return {
        "report_date": report_date.isoformat(),
        "total_shortages": len(alerts),
        "total_projects": len(project_list),
        "projects": project_list
    }


@router.get("/cause-analysis")
def get_shortage_cause_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料原因分析
    """
    query = db.query(MaterialShortage)
    
    if project_id:
        query = query.filter(MaterialShortage.project_id == project_id)
    
    if start_date:
        query = query.filter(func.date(MaterialShortage.created_at) >= start_date)
    
    if end_date:
        query = query.filter(func.date(MaterialShortage.created_at) <= end_date)
    
    alerts = query.all()
    
    # 分析缺料原因（根据解决方案字段）
    cause_stats = {
        "purchase_delay": 0,  # 采购延迟
        "supplier_delay": 0,  # 供应商延迟
        "inventory_shortage": 0,  # 库存不足
        "planning_error": 0,  # 计划错误
        "other": 0  # 其他
    }
    
    for alert in alerts:
        solution = alert.solution or ""
        solution_lower = solution.lower()
        
        if "采购" in solution or "purchase" in solution_lower:
            cause_stats["purchase_delay"] += 1
        elif "供应商" in solution or "supplier" in solution_lower:
            cause_stats["supplier_delay"] += 1
        elif "库存" in solution or "inventory" in solution_lower:
            cause_stats["inventory_shortage"] += 1
        elif "计划" in solution or "planning" in solution_lower:
            cause_stats["planning_error"] += 1
        else:
            cause_stats["other"] += 1
    
    total = len(alerts)
    
    return {
        "total_shortages": total,
        "cause_distribution": cause_stats,
        "cause_percentage": {
            "purchase_delay": round((cause_stats["purchase_delay"] / total * 100) if total > 0 else 0, 2),
            "supplier_delay": round((cause_stats["supplier_delay"] / total * 100) if total > 0 else 0, 2),
            "inventory_shortage": round((cause_stats["inventory_shortage"] / total * 100) if total > 0 else 0, 2),
            "planning_error": round((cause_stats["planning_error"] / total * 100) if total > 0 else 0, 2),
            "other": round((cause_stats["other"] / total * 100) if total > 0 else 0, 2)
        }
    }


# ==================== 缺料上报 ====================

def generate_shortage_report_no(db: Session) -> str:
    """生成缺料上报单号：SR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_report = (
        db.query(ShortageReport)
        .filter(ShortageReport.report_no.like(f"SR-{today}-%"))
        .order_by(desc(ShortageReport.report_no))
        .first()
    )
    if max_report:
        seq = int(max_report.report_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"SR-{today}-{seq:03d}"


@router.get("/reports", response_model=PaginatedResponse, status_code=200)
def read_shortage_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    urgent_level: Optional[str] = Query(None, description="紧急程度筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料上报列表
    """
    query = db.query(ShortageReport)
    
    if project_id:
        query = query.filter(ShortageReport.project_id == project_id)
    if status:
        query = query.filter(ShortageReport.status == status)
    if urgent_level:
        query = query.filter(ShortageReport.urgent_level == urgent_level)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(ShortageReport.report_time)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        machine = None
        if report.machine_id:
            machine = db.query(Machine).filter(Machine.id == report.machine_id).first()
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        
        items.append(ShortageReportResponse(
            id=report.id,
            report_no=report.report_no,
            project_id=report.project_id,
            project_name=project.project_name if project else None,
            machine_id=report.machine_id,
            machine_name=machine.machine_name if machine else None,
            work_order_id=report.work_order_id,
            material_id=report.material_id,
            material_code=report.material_code,
            material_name=report.material_name,
            required_qty=report.required_qty,
            shortage_qty=report.shortage_qty,
            urgent_level=report.urgent_level,
            status=report.status,
            reporter_id=report.reporter_id,
            reporter_name=reporter.real_name or reporter.username if reporter else None,
            report_time=report.report_time,
            confirmed_by=report.confirmed_by,
            confirmed_at=report.confirmed_at,
            handler_id=report.handler_id,
            resolved_at=report.resolved_at,
            solution_type=report.solution_type,
            solution_note=report.solution_note,
            remark=report.remark,
            created_at=report.created_at,
            updated_at=report.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/reports", response_model=ShortageReportResponse, status_code=201)
def create_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ShortageReportCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建缺料上报（车间扫码上报）
    """
    project = db.query(Project).filter(Project.id == report_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if report_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == report_in.machine_id).first()
        if not machine or machine.project_id != report_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")
    
    material = db.query(Material).filter(Material.id == report_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    report_no = generate_shortage_report_no(db)
    
    report = ShortageReport(
        report_no=report_no,
        project_id=report_in.project_id,
        machine_id=report_in.machine_id,
        work_order_id=report_in.work_order_id,
        material_id=report_in.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        required_qty=report_in.required_qty,
        shortage_qty=report_in.shortage_qty,
        urgent_level=report_in.urgent_level,
        status="REPORTED",
        reporter_id=current_user.id,
        report_location=report_in.report_location,
        remark=report_in.remark
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report.id, db, current_user)


@router.get("/reports/{report_id}", response_model=ShortageReportResponse, status_code=200)
def read_shortage_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    上报详情
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    project = db.query(Project).filter(Project.id == report.project_id).first()
    machine = None
    if report.machine_id:
        machine = db.query(Machine).filter(Machine.id == report.machine_id).first()
    reporter = db.query(User).filter(User.id == report.reporter_id).first()
    
    return ShortageReportResponse(
        id=report.id,
        report_no=report.report_no,
        project_id=report.project_id,
        project_name=project.project_name if project else None,
        machine_id=report.machine_id,
        machine_name=machine.machine_name if machine else None,
        work_order_id=report.work_order_id,
        material_id=report.material_id,
        material_code=report.material_code,
        material_name=report.material_name,
        required_qty=report.required_qty,
        shortage_qty=report.shortage_qty,
        urgent_level=report.urgent_level,
        status=report.status,
        reporter_id=report.reporter_id,
        reporter_name=reporter.real_name or reporter.username if reporter else None,
        report_time=report.report_time,
        confirmed_by=report.confirmed_by,
        confirmed_at=report.confirmed_at,
        handler_id=report.handler_id,
        resolved_at=report.resolved_at,
        solution_type=report.solution_type,
        solution_note=report.solution_note,
        remark=report.remark,
        created_at=report.created_at,
        updated_at=report.updated_at
    )


@router.put("/reports/{report_id}/confirm", response_model=ShortageReportResponse, status_code=200)
def confirm_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    确认上报（仓管确认）
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status != "REPORTED":
        raise HTTPException(status_code=400, detail="只能确认已上报状态的记录")
    
    report.status = "CONFIRMED"
    report.confirmed_by = current_user.id
    report.confirmed_at = datetime.now()
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report_id, db, current_user)


@router.put("/reports/{report_id}/handle", response_model=ShortageReportResponse, status_code=200)
def handle_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    solution_type: str = Query(..., description="解决方案类型：PURCHASE/SUBSTITUTE/TRANSFER/OTHER"),
    solution_note: Optional[str] = Query(None, description="解决方案说明"),
    handler_id: Optional[int] = Query(None, description="处理人ID"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    处理上报
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status not in ["CONFIRMED", "HANDLING"]:
        raise HTTPException(status_code=400, detail="只能处理已确认或处理中状态的记录")
    
    report.status = "HANDLING"
    report.solution_type = solution_type
    report.solution_note = solution_note
    report.handler_id = handler_id or current_user.id
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report_id, db, current_user)


@router.put("/reports/{report_id}/resolve", response_model=ShortageReportResponse, status_code=200)
def resolve_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:resolve")),
) -> Any:
    """
    解决上报
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status != "HANDLING":
        raise HTTPException(status_code=400, detail="只能解决处理中状态的记录")
    
    report.status = "RESOLVED"
    report.resolved_at = datetime.now()
    if not report.handler_id:
        report.handler_id = current_user.id
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report_id, db, current_user)


# ==================== 到货跟踪 ====================

def generate_arrival_no(db: Session) -> str:
    """生成到货跟踪单号：AR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_arrival = (
        db.query(MaterialArrival)
        .filter(MaterialArrival.arrival_no.like(f"AR-{today}-%"))
        .order_by(desc(MaterialArrival.arrival_no))
        .first()
    )
    if max_arrival:
        seq = int(max_arrival.arrival_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"AR-{today}-{seq:03d}"


@router.get("/arrivals", response_model=PaginatedResponse, status_code=200)
def read_material_arrivals(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    shortage_report_id: Optional[int] = Query(None, description="缺料上报ID筛选"),
    purchase_order_id: Optional[int] = Query(None, description="采购订单ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    is_delayed: Optional[bool] = Query(None, description="是否延迟筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    到货跟踪列表
    """
    query = db.query(MaterialArrival)
    
    if shortage_report_id:
        query = query.filter(MaterialArrival.shortage_report_id == shortage_report_id)
    if purchase_order_id:
        query = query.filter(MaterialArrival.purchase_order_id == purchase_order_id)
    if status:
        query = query.filter(MaterialArrival.status == status)
    if is_delayed is not None:
        query = query.filter(MaterialArrival.is_delayed == is_delayed)
    
    total = query.count()
    offset = (page - 1) * page_size
    arrivals = query.order_by(MaterialArrival.expected_date).offset(offset).limit(page_size).all()
    
    items = []
    for arrival in arrivals:
        from app.models.material import Supplier
        supplier = None
        if arrival.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == arrival.supplier_id).first()
        
        items.append(MaterialArrivalResponse(
            id=arrival.id,
            arrival_no=arrival.arrival_no,
            shortage_report_id=arrival.shortage_report_id,
            purchase_order_id=arrival.purchase_order_id,
            material_id=arrival.material_id,
            material_code=arrival.material_code,
            material_name=arrival.material_name,
            expected_qty=arrival.expected_qty,
            supplier_id=arrival.supplier_id,
            supplier_name=supplier.supplier_name if supplier else arrival.supplier_name,
            expected_date=arrival.expected_date,
            actual_date=arrival.actual_date,
            is_delayed=arrival.is_delayed,
            delay_days=arrival.delay_days,
            status=arrival.status,
            received_qty=arrival.received_qty or Decimal("0"),
            received_by=arrival.received_by,
            received_at=arrival.received_at,
            follow_up_count=arrival.follow_up_count,
            remark=arrival.remark,
            created_at=arrival.created_at,
            updated_at=arrival.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/arrivals", response_model=MaterialArrivalResponse, status_code=201)
def create_material_arrival(
    *,
    db: Session = Depends(deps.get_db),
    shortage_report_id: Optional[int] = Query(None, description="缺料上报ID"),
    purchase_order_item_id: Optional[int] = Query(None, description="采购订单明细ID"),
    material_id: int = Query(..., description="物料ID"),
    expected_qty: Decimal = Query(..., gt=0, description="预期到货数量"),
    expected_date: date = Query(..., description="预期到货日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建交付记录（从采购订单或缺料上报创建）
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    purchase_order_id = None
    if purchase_order_item_id:
        po_item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == purchase_order_item_id).first()
        if not po_item:
            raise HTTPException(status_code=404, detail="采购订单明细不存在")
        purchase_order_id = po_item.order_id
    
    if shortage_report_id:
        report = db.query(ShortageReport).filter(ShortageReport.id == shortage_report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    from app.models.material import Supplier
    supplier_name = None
    if supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        supplier_name = supplier.supplier_name if supplier else None
    
    arrival_no = generate_arrival_no(db)
    
    arrival = MaterialArrival(
        arrival_no=arrival_no,
        shortage_report_id=shortage_report_id,
        purchase_order_id=purchase_order_id,
        purchase_order_item_id=purchase_order_item_id,
        material_id=material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        expected_qty=expected_qty,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        expected_date=expected_date,
        status="PENDING"
    )
    
    db.add(arrival)
    db.commit()
    db.refresh(arrival)
    
    return read_material_arrival(arrival.id, db, current_user)


@router.get("/arrivals/{arrival_id}", response_model=MaterialArrivalResponse, status_code=200)
def read_material_arrival(
    arrival_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    到货跟踪详情
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")
    
    from app.models.material import Supplier
    supplier = None
    if arrival.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == arrival.supplier_id).first()
    
    return MaterialArrivalResponse(
        id=arrival.id,
        arrival_no=arrival.arrival_no,
        shortage_report_id=arrival.shortage_report_id,
        purchase_order_id=arrival.purchase_order_id,
        material_id=arrival.material_id,
        material_code=arrival.material_code,
        material_name=arrival.material_name,
        expected_qty=arrival.expected_qty,
        supplier_id=arrival.supplier_id,
        supplier_name=supplier.supplier_name if supplier else arrival.supplier_name,
        expected_date=arrival.expected_date,
        actual_date=arrival.actual_date,
        is_delayed=arrival.is_delayed,
        delay_days=arrival.delay_days,
        status=arrival.status,
        received_qty=arrival.received_qty or Decimal("0"),
        received_by=arrival.received_by,
        received_at=arrival.received_at,
        follow_up_count=arrival.follow_up_count,
        remark=arrival.remark,
        created_at=arrival.created_at,
        updated_at=arrival.updated_at
    )


@router.put("/arrivals/{arrival_id}/status", response_model=MaterialArrivalResponse, status_code=200)
def update_arrival_status(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    status: str = Query(..., description="状态：PENDING/IN_TRANSIT/DELAYED/RECEIVED/CANCELLED"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    更新到货状态
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")
    
    arrival.status = status
    
    # 如果标记为延迟，计算延迟天数
    if status == "DELAYED" and arrival.expected_date:
        today = datetime.now().date()
        if today > arrival.expected_date:
            arrival.is_delayed = True
            arrival.delay_days = (today - arrival.expected_date).days
    
    db.add(arrival)
    db.commit()
    db.refresh(arrival)
    
    return read_material_arrival(arrival_id, db, current_user)


@router.post("/arrivals/{arrival_id}/follow-up", response_model=ResponseModel, status_code=201)
def create_arrival_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    follow_up_in: ArrivalFollowUpCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    创建跟催记录
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")
    
    follow_up = ArrivalFollowUp(
        arrival_id=arrival_id,
        follow_up_type=follow_up_in.follow_up_type,
        follow_up_note=follow_up_in.follow_up_note,
        supplier_response=follow_up_in.supplier_response,
        next_follow_up_date=follow_up_in.next_follow_up_date,
        followed_by=current_user.id
    )
    
    arrival.follow_up_count = (arrival.follow_up_count or 0) + 1
    arrival.last_follow_up_at = datetime.now()
    
    db.add(follow_up)
    db.add(arrival)
    db.commit()
    
    return ResponseModel(message="跟催记录创建成功")


@router.post("/arrivals/{arrival_id}/receive", response_model=MaterialArrivalResponse, status_code=200)
def receive_material_arrival(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    received_qty: Decimal = Query(..., gt=0, description="实收数量"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    确认收货
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")
    
    if arrival.status == "RECEIVED":
        raise HTTPException(status_code=400, detail="已经收货")
    
    arrival.status = "RECEIVED"
    arrival.received_qty = received_qty
    arrival.received_by = current_user.id
    arrival.received_at = datetime.now()
    arrival.actual_date = datetime.now().date()
    
    # 更新延迟状态
    if arrival.expected_date and arrival.actual_date > arrival.expected_date:
        arrival.is_delayed = True
        arrival.delay_days = (arrival.actual_date - arrival.expected_date).days
    
    db.add(arrival)
    db.commit()
    db.refresh(arrival)
    
    return read_material_arrival(arrival_id, db, current_user)


# ==================== 物料替代 ====================

def generate_substitution_no(db: Session) -> str:
    """生成物料替代单号：MS-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_sub = (
        db.query(MaterialSubstitution)
        .filter(MaterialSubstitution.substitution_no.like(f"MS-{today}-%"))
        .order_by(desc(MaterialSubstitution.substitution_no))
        .first()
    )
    if max_sub:
        seq = int(max_sub.substitution_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"MS-{today}-{seq:03d}"


@router.get("/substitutions", response_model=PaginatedResponse, status_code=200)
def read_material_substitutions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    替代申请列表
    """
    query = db.query(MaterialSubstitution)
    
    if project_id:
        query = query.filter(MaterialSubstitution.project_id == project_id)
    if status:
        query = query.filter(MaterialSubstitution.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    substitutions = query.order_by(desc(MaterialSubstitution.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for sub in substitutions:
        project = db.query(Project).filter(Project.id == sub.project_id).first()
        tech_approver_name = None
        if sub.tech_approver_id:
            tech_approver = db.query(User).filter(User.id == sub.tech_approver_id).first()
            tech_approver_name = tech_approver.real_name or tech_approver.username if tech_approver else None
        prod_approver_name = None
        if sub.prod_approver_id:
            prod_approver = db.query(User).filter(User.id == sub.prod_approver_id).first()
            prod_approver_name = prod_approver.real_name or prod_approver.username if prod_approver else None
        
        items.append(MaterialSubstitutionResponse(
            id=sub.id,
            substitution_no=sub.substitution_no,
            project_id=sub.project_id,
            project_name=project.project_name if project else None,
            original_material_id=sub.original_material_id,
            original_material_code=sub.original_material_code,
            original_material_name=sub.original_material_name,
            original_qty=sub.original_qty,
            substitute_material_id=sub.substitute_material_id,
            substitute_material_code=sub.substitute_material_code,
            substitute_material_name=sub.substitute_material_name,
            substitute_qty=sub.substitute_qty,
            substitution_reason=sub.substitution_reason,
            technical_impact=sub.technical_impact,
            cost_impact=sub.cost_impact or Decimal("0"),
            status=sub.status,
            tech_approver_id=sub.tech_approver_id,
            tech_approver_name=tech_approver_name,
            tech_approved_at=sub.tech_approved_at,
            prod_approver_id=sub.prod_approver_id,
            prod_approver_name=prod_approver_name,
            prod_approved_at=sub.prod_approved_at,
            executed_at=sub.executed_at,
            remark=sub.remark,
            created_at=sub.created_at,
            updated_at=sub.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/substitutions", response_model=MaterialSubstitutionResponse, status_code=201)
def create_material_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_in: MaterialSubstitutionCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建替代申请
    """
    project = db.query(Project).filter(Project.id == sub_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    original_material = db.query(Material).filter(Material.id == sub_in.original_material_id).first()
    if not original_material:
        raise HTTPException(status_code=404, detail="原物料不存在")
    
    substitute_material = db.query(Material).filter(Material.id == sub_in.substitute_material_id).first()
    if not substitute_material:
        raise HTTPException(status_code=404, detail="替代物料不存在")
    
    if sub_in.original_material_id == sub_in.substitute_material_id:
        raise HTTPException(status_code=400, detail="原物料和替代物料不能相同")
    
    substitution_no = generate_substitution_no(db)
    
    substitution = MaterialSubstitution(
        substitution_no=substitution_no,
        shortage_report_id=sub_in.shortage_report_id,
        project_id=sub_in.project_id,
        bom_item_id=sub_in.bom_item_id,
        original_material_id=sub_in.original_material_id,
        original_material_code=original_material.material_code,
        original_material_name=original_material.material_name,
        original_qty=sub_in.original_qty,
        substitute_material_id=sub_in.substitute_material_id,
        substitute_material_code=substitute_material.material_code,
        substitute_material_name=substitute_material.material_name,
        substitute_qty=sub_in.substitute_qty,
        substitution_reason=sub_in.substitution_reason,
        technical_impact=sub_in.technical_impact,
        cost_impact=sub_in.cost_impact or Decimal("0"),
        status="DRAFT",
        created_by=current_user.id,
        remark=sub_in.remark
    )
    
    db.add(substitution)
    db.commit()
    db.refresh(substitution)
    
    return read_material_substitution(substitution.id, db, current_user)


@router.get("/substitutions/{sub_id}", response_model=MaterialSubstitutionResponse, status_code=200)
def read_material_substitution(
    sub_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    物料替代详情
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")
    
    project = db.query(Project).filter(Project.id == sub.project_id).first()
    tech_approver_name = None
    if sub.tech_approver_id:
        tech_approver = db.query(User).filter(User.id == sub.tech_approver_id).first()
        tech_approver_name = tech_approver.real_name or tech_approver.username if tech_approver else None
    prod_approver_name = None
    if sub.prod_approver_id:
        prod_approver = db.query(User).filter(User.id == sub.prod_approver_id).first()
        prod_approver_name = prod_approver.real_name or prod_approver.username if prod_approver else None
    
    return MaterialSubstitutionResponse(
        id=sub.id,
        substitution_no=sub.substitution_no,
        project_id=sub.project_id,
        project_name=project.project_name if project else None,
        original_material_id=sub.original_material_id,
        original_material_code=sub.original_material_code,
        original_material_name=sub.original_material_name,
        original_qty=sub.original_qty,
        substitute_material_id=sub.substitute_material_id,
        substitute_material_code=sub.substitute_material_code,
        substitute_material_name=sub.substitute_material_name,
        substitute_qty=sub.substitute_qty,
        substitution_reason=sub.substitution_reason,
        technical_impact=sub.technical_impact,
        cost_impact=sub.cost_impact or Decimal("0"),
        status=sub.status,
        tech_approver_id=sub.tech_approver_id,
        tech_approver_name=tech_approver_name,
        tech_approved_at=sub.tech_approved_at,
        prod_approver_id=sub.prod_approver_id,
        prod_approver_name=prod_approver_name,
        prod_approved_at=sub.prod_approved_at,
        executed_at=sub.executed_at,
        remark=sub.remark,
        created_at=sub.created_at,
        updated_at=sub.updated_at
    )


@router.put("/substitutions/{sub_id}/tech-approve", response_model=MaterialSubstitutionResponse, status_code=200)
def tech_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_id: int,
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    技术审批
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")
    
    if sub.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能审批草稿状态的替代申请")
    
    sub.status = "TECH_PENDING"
    sub.tech_approver_id = current_user.id
    sub.tech_approved_at = datetime.now()
    sub.tech_approval_note = approval_note
    
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return read_material_substitution(sub_id, db, current_user)


@router.put("/substitutions/{sub_id}/prod-approve", response_model=MaterialSubstitutionResponse, status_code=200)
def prod_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_id: int,
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    生产审批
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")
    
    if sub.status != "TECH_PENDING":
        raise HTTPException(status_code=400, detail="只能审批技术已审批状态的替代申请")
    
    sub.status = "PROD_PENDING"
    sub.prod_approver_id = current_user.id
    sub.prod_approved_at = datetime.now()
    sub.prod_approval_note = approval_note
    
    # 如果技术审批和生产审批都完成，自动更新为已审批
    if sub.tech_approved_at and sub.prod_approved_at:
        sub.status = "APPROVED"
    
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return read_material_substitution(sub_id, db, current_user)


@router.put("/substitutions/{sub_id}/execute", response_model=MaterialSubstitutionResponse, status_code=200)
def execute_substitution(
    *,
    db: Session = Depends(deps.get_db),
    sub_id: int,
    execution_note: Optional[str] = Query(None, description="执行说明"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    执行替代
    """
    sub = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="物料替代不存在")
    
    if sub.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能执行已审批状态的替代申请")
    
    sub.status = "EXECUTED"
    sub.executed_at = datetime.now()
    sub.executed_by = current_user.id
    sub.execution_note = execution_note
    
    # TODO: 更新BOM中的物料信息
    
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return read_material_substitution(sub_id, db, current_user)


# ==================== 物料调拨 ====================

def generate_transfer_no(db: Session) -> str:
    """生成物料调拨单号：MT-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_transfer = (
        db.query(MaterialTransfer)
        .filter(MaterialTransfer.transfer_no.like(f"MT-{today}-%"))
        .order_by(desc(MaterialTransfer.transfer_no))
        .first()
    )
    if max_transfer:
        seq = int(max_transfer.transfer_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"MT-{today}-{seq:03d}"


@router.get("/transfers", response_model=PaginatedResponse, status_code=200)
def read_material_transfers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    from_project_id: Optional[int] = Query(None, description="调出项目ID筛选"),
    to_project_id: Optional[int] = Query(None, description="调入项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    调拨申请列表
    """
    query = db.query(MaterialTransfer)
    
    if from_project_id:
        query = query.filter(MaterialTransfer.from_project_id == from_project_id)
    if to_project_id:
        query = query.filter(MaterialTransfer.to_project_id == to_project_id)
    if status:
        query = query.filter(MaterialTransfer.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    transfers = query.order_by(desc(MaterialTransfer.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for transfer in transfers:
        from_project = None
        if transfer.from_project_id:
            from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
        to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
        approver_name = None
        if transfer.approver_id:
            approver = db.query(User).filter(User.id == transfer.approver_id).first()
            approver_name = approver.real_name or approver.username if approver else None
        
        items.append(MaterialTransferResponse(
            id=transfer.id,
            transfer_no=transfer.transfer_no,
            from_project_id=transfer.from_project_id,
            from_project_name=from_project.project_name if from_project else None,
            from_location=transfer.from_location,
            to_project_id=transfer.to_project_id,
            to_project_name=to_project.project_name if to_project else None,
            to_location=transfer.to_location,
            material_id=transfer.material_id,
            material_code=transfer.material_code,
            material_name=transfer.material_name,
            transfer_qty=transfer.transfer_qty,
            available_qty=transfer.available_qty or Decimal("0"),
            transfer_reason=transfer.transfer_reason,
            urgent_level=transfer.urgent_level,
            status=transfer.status,
            approver_id=transfer.approver_id,
            approver_name=approver_name,
            approved_at=transfer.approved_at,
            executed_at=transfer.executed_at,
            actual_qty=transfer.actual_qty,
            remark=transfer.remark,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/transfers", response_model=MaterialTransferResponse, status_code=201)
def create_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_in: MaterialTransferCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建调拨申请
    """
    to_project = db.query(Project).filter(Project.id == transfer_in.to_project_id).first()
    if not to_project:
        raise HTTPException(status_code=404, detail="调入项目不存在")
    
    if transfer_in.from_project_id:
        from_project = db.query(Project).filter(Project.id == transfer_in.from_project_id).first()
        if not from_project:
            raise HTTPException(status_code=404, detail="调出项目不存在")
    
    material = db.query(Material).filter(Material.id == transfer_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # 检查可调拨数量（从调出项目的库存）
    available_qty = Decimal("0")
    if transfer_in.from_project_id:
        # 查询调出项目的物料库存
        from app.services.material_transfer_service import material_transfer_service
        stock_info = material_transfer_service.get_project_material_stock(
            db, transfer_in.from_project_id, transfer_in.material_id
        )
        available_qty = stock_info["available_qty"]

    if transfer_in.transfer_qty > available_qty:
        raise HTTPException(status_code=400, detail=f"可调拨数量不足，当前可用：{available_qty}（来源：{stock_info.get('source', '未知')}）")
    
    transfer_no = generate_transfer_no(db)
    
    transfer = MaterialTransfer(
        transfer_no=transfer_no,
        shortage_report_id=transfer_in.shortage_report_id,
        from_project_id=transfer_in.from_project_id,
        from_location=transfer_in.from_location,
        to_project_id=transfer_in.to_project_id,
        to_location=transfer_in.to_location,
        material_id=transfer_in.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        transfer_qty=transfer_in.transfer_qty,
        available_qty=available_qty,
        transfer_reason=transfer_in.transfer_reason,
        urgent_level=transfer_in.urgent_level,
        status="DRAFT",
        created_by=current_user.id,
        remark=transfer_in.remark
    )
    
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    
    return read_material_transfer(transfer.id, db, current_user)


@router.get("/transfers/{transfer_id}", response_model=MaterialTransferResponse, status_code=200)
def read_material_transfer(
    transfer_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    物料调拨详情
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")
    
    from_project = None
    if transfer.from_project_id:
        from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver_name = None
    if transfer.approver_id:
        approver = db.query(User).filter(User.id == transfer.approver_id).first()
        approver_name = approver.real_name or approver.username if approver else None
    
    return MaterialTransferResponse(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        from_project_id=transfer.from_project_id,
        from_project_name=from_project.project_name if from_project else None,
        from_location=transfer.from_location,
        to_project_id=transfer.to_project_id,
        to_project_name=to_project.project_name if to_project else None,
        to_location=transfer.to_location,
        material_id=transfer.material_id,
        material_code=transfer.material_code,
        material_name=transfer.material_name,
        transfer_qty=transfer.transfer_qty,
        available_qty=transfer.available_qty or Decimal("0"),
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver_name,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at
    )


@router.put("/transfers/{transfer_id}/approve", response_model=MaterialTransferResponse, status_code=200)
def approve_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    调拨审批
    """
    from app.services.material_transfer_service import material_transfer_service
    from app.services.notification_service import notification_service, NotificationType, NotificationPriority

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if transfer.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能审批草稿状态的调拨申请")

    # 执行前校验（确保调拨后库存足够）
    validation = material_transfer_service.validate_transfer_before_execute(db, transfer)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail="; ".join(validation["errors"]))

    transfer.status = "APPROVED"
    transfer.approver_id = current_user.id
    transfer.approved_at = datetime.now()
    transfer.approval_note = approval_note

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # 发送审批通过通知
    try:
        notification_service.send_notification(
            db=db,
            recipient_id=transfer.created_by,
            notification_type=NotificationType.TASK_APPROVED,
            title=f"物料调拨申请已批准: {transfer.material_name}",
            content=f"调拨单号: {transfer.transfer_no}\n审批人: {current_user.real_name or current_user.username}",
            priority=NotificationPriority.NORMAL,
            link=f"/shortage-alerts/transfers/{transfer.id}"
        )
    except Exception:
        pass

    # 如果有调出项目，也通知调出项目负责人
    if transfer.from_project_id:
        try:
            from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
            if from_project and from_project.pm_id:
                notification_service.send_notification(
                    db=db,
                    recipient_id=from_project.pm_id,
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"物料调出申请已批准: {transfer.material_name}",
                    content=f"调拨单号: {transfer.transfer_no}\n调入项目: {transfer.to_project_id}",
                    priority=NotificationPriority.HIGH,
                    link=f"/shortage-alerts/transfers/{transfer.id}"
                )
        except Exception:
            pass

    return read_material_transfer(transfer_id, db, current_user)


@router.put("/transfers/{transfer_id}/execute", response_model=MaterialTransferResponse, status_code=200)
def execute_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    actual_qty: Optional[Decimal] = Query(None, description="实际调拨数量"),
    execution_note: Optional[str] = Query(None, description="执行说明"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    执行调拨
    """
    from app.services.material_transfer_service import material_transfer_service

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if transfer.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能执行已审批状态的调拨申请")

    # 执行前校验
    validation = material_transfer_service.validate_transfer_before_execute(db, transfer)
    if not validation["is_valid"]:
        raise HTTPException(status_code=400, detail="; ".join(validation["errors"]))

    # 更新状态和执行信息
    transfer.status = "EXECUTED"
    transfer.executed_at = datetime.now()
    transfer.executed_by = current_user.id
    transfer.actual_qty = actual_qty or transfer.transfer_qty
    transfer.execution_note = execution_note

    # 更新项目库存（从调出项目减少，调入项目增加）
    stock_updates = material_transfer_service.execute_stock_update(
        db, transfer, actual_qty
    )

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # 发送通知
    from app.services.notification_service import notification_service, NotificationType, NotificationPriority
    try:
        # 通知调入项目负责人
        notification_service.send_notification(
            db=db,
            recipient_id=transfer.created_by,
            notification_type=NotificationType.TASK_COMPLETED,
            title=f"物料调拨已完成: {transfer.material_name}",
            content=f"调拨单号: {transfer.transfer_no}\n实际调拨数量: {transfer.actual_qty}",
            priority=NotificationPriority.NORMAL,
            link=f="/shortage-alerts/transfers/{transfer.id}"
        )
    except Exception:
        pass

    result = read_material_transfer(transfer_id, db, current_user)
    # 添加库存更新信息
    result.stock_updates = stock_updates

    return result


@router.get("/transfers/suggest-sources", response_model=ResponseModel, status_code=200)
def suggest_transfer_sources(
    *,
    db: Session = Depends(deps.get_db),
    to_project_id: int = Query(..., description="调入项目ID"),
    material_id: int = Query(..., description="物料ID"),
    required_qty: Decimal = Query(..., description="需要数量"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    推荐物料调拨来源

    根据需要的物料和数量，推荐有库存的项目或仓库
    """
    from app.services.material_transfer_service import material_transfer_service

    suggestions = material_transfer_service.suggest_transfer_sources(
        db, to_project_id, material_id, required_qty
    )

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "to_project_id": to_project_id,
            "material_id": material_id,
            "required_qty": float(required_qty),
            "suggestions": suggestions,
            "total_sources": len(suggestions),
            "can_fully_supply": sum(1 for s in suggestions if s["can_fully_supply"])
        }
    )


@router.get("/transfers/{transfer_id}/stock-check", response_model=ResponseModel, status_code=200)
def check_transfer_stock(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    检查调拨单的库存状态

    返回调出项目的当前可用库存，用于确认是否可以执行调拨
    """
    from app.services.material_transfer_service import material_transfer_service

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if not transfer.from_project_id:
        return ResponseModel(
            code=200,
            message="无调出项目（从仓库调拨）",
            data={"from_project": None, "stock_info": None}
        )

    stock_info = material_transfer_service.get_project_material_stock(
        db, transfer.from_project_id, transfer.material_id
    )

    check_result = material_transfer_service.check_transfer_available(
        db,
        transfer.from_project_id,
        transfer.material_id,
        transfer.transfer_qty
    )

    return ResponseModel(
        code=200,
        message="库存检查完成",
        data={
            "from_project_id": transfer.from_project_id,
            "material_id": transfer.material_id,
            "material_code": transfer.material_code,
            "material_name": transfer.material_name,
            "stock_info": stock_info,
            "transfer_qty": float(transfer.transfer_qty),
            "check_result": check_result
        }
    )


@router.put("/transfers/{transfer_id}/reject", response_model=MaterialTransferResponse, status_code=200)
def reject_material_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    驳回调拨申请
    """
    from app.services.notification_service import notification_service, NotificationType, NotificationPriority

    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="物料调拨不存在")

    if transfer.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能驳回草稿状态的调拨申请")

    transfer.status = "REJECTED"
    transfer.approver_id = current_user.id
    transfer.approved_at = datetime.now()
    transfer.approval_note = rejection_reason

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # 发送驳回通知
    try:
        notification_service.send_notification(
            db=db,
            recipient_id=transfer.created_by,
            notification_type=NotificationType.TASK_REJECTED,
            title=f"物料调拨申请已驳回: {transfer.material_name}",
            content=f"调拨单号: {transfer.transfer_no}\n驳回原因: {rejection_reason}",
            priority=NotificationPriority.HIGH,
            link=f"/shortage-alerts/transfers/{transfer.id}"
        )
    except Exception:
        pass

    return read_material_transfer(transfer_id, db, current_user)

