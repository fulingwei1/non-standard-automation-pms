# -*- coding: utf-8 -*-
"""
齐套率优化 API 端点
1. 缺料自动催货
2. 替代料推荐
3. 安全库存预警
4. 齐套率改进建议
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.schemas import success_response
from app.models.user import User
from app.schemas.kitting_optimization import (
    AlternativeListResponse,
    ExpediteRequest,
    ExpediteResult,
    ExpediteStats,
    KittingImprovementSuggestions,
    SafetyStockAlertResponse,
)
from app.services.kitting_optimization_service import KittingOptimizationService

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== 1. 缺料自动催货 ====================


@router.post("/kitting/expedite", summary="缺料自动催货")
def create_expedite(
    request: ExpediteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量生成催货通知

    功能:
    - 手动指定催货目标（物料+订单）
    - 自动识别高风险缺料（关键物料、需求日期临近、大比例缺料）
    - 生成催货通知记录（后续对接邮件/短信/微信）
    - 避免重复催货（3天内同一物料+缺料单不重复）
    """
    try:
        svc = KittingOptimizationService(db)

        # 自动识别高风险缺料
        auto_high_risk = []
        if request.auto_detect_high_risk:
            auto_high_risk = svc.detect_high_risk_shortages(
                project_id=request.project_id
            )

        # 创建催货记录
        targets = [t.model_dump() for t in request.targets]
        records = svc.create_expedite_records(
            targets=targets,
            notify_methods=request.notify_methods,
            auto_high_risk=auto_high_risk,
            user_id=current_user.id,
        )

        # 构建响应
        record_list = []
        notify_sent = 0
        notify_pending = 0
        for r in records:
            vendor_name = None
            if r.vendor:
                vendor_name = r.vendor.supplier_name
            record_list.append({
                "id": r.id,
                "material_id": r.material_id,
                "material_code": r.material_code,
                "material_name": r.material_name,
                "supplier_id": r.supplier_id,
                "supplier_name": vendor_name,
                "purchase_order_id": r.purchase_order_id,
                "shortage_id": r.shortage_id,
                "urgency_level": r.urgency_level,
                "shortage_qty": float(r.shortage_qty) if r.shortage_qty else None,
                "required_date": r.required_date,
                "original_promised_date": r.original_promised_date,
                "new_promised_date": r.new_promised_date,
                "notify_method": r.notify_method,
                "notify_status": r.notify_status,
                "status": r.status,
                "supplier_response": r.supplier_response,
                "actual_delivery_date": r.actual_delivery_date,
                "is_on_time": r.is_on_time,
                "created_at": r.created_at,
                "remark": r.remark,
            })
            if r.notify_status == "SENT":
                notify_sent += 1
            else:
                notify_pending += 1

        result = {
            "total_created": len(records),
            "auto_detected": len(auto_high_risk),
            "notify_sent": notify_sent,
            "notify_pending": notify_pending,
            "records": record_list,
        }

        return success_response(data=result, message=f"已创建{len(records)}条催货记录")

    except Exception as e:
        logger.exception("创建催货记录失败")
        raise HTTPException(status_code=500, detail=f"创建催货记录失败: {str(e)}")


@router.get("/kitting/expedite/stats", summary="催货效果统计")
def get_expedite_stats(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    催货效果统计

    返回：催后准时率、平均响应天数、按紧急程度/供应商分布
    """
    try:
        svc = KittingOptimizationService(db)
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        stats = svc.get_expedite_stats(start_date=start, end_date=end)
        return success_response(data=stats)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        logger.exception("获取催货统计失败")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 2. 替代料推荐 ====================


@router.get("/materials/{material_id}/alternatives", summary="替代料推荐")
def get_material_alternatives(
    material_id: int,
    include_unverified: bool = Query(True, description="是否包含未验证的替代料"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取物料的替代料推荐

    功能:
    - 已登记替代料（经过验证的）
    - 基于规格参数自动匹配（同分类+相似规格）
    - 替代料库存和价格对比
    - ECN变更关联
    """
    try:
        svc = KittingOptimizationService(db)
        result = svc.get_alternatives(
            material_id=material_id,
            include_unverified=include_unverified,
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return success_response(data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取替代料推荐失败")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 3. 安全库存预警 ====================


@router.get("/inventory/safety-stock-alerts", summary="安全库存预警")
def get_safety_stock_alerts(
    alert_level: Optional[str] = Query(
        None, description="预警级别过滤: CRITICAL/WARNING/INFO"
    ),
    category_id: Optional[int] = Query(None, description="物料分类ID"),
    only_key_materials: bool = Query(False, description="仅关键物料"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    安全库存预警

    功能:
    - 基于历史消耗计算安全库存水位
    - 低于安全库存自动预警（CRITICAL/WARNING/INFO 三级）
    - 建议补货数量（考虑采购周期+消耗速率+最小订购量）
    - 预计断料日期
    - 高频缺料物料标记
    """
    try:
        if alert_level and alert_level not in ("CRITICAL", "WARNING", "INFO"):
            raise HTTPException(
                status_code=400,
                detail="alert_level 必须为 CRITICAL/WARNING/INFO",
            )

        svc = KittingOptimizationService(db)
        result = svc.get_safety_stock_alerts(
            alert_level=alert_level,
            category_id=category_id,
            only_key_materials=only_key_materials,
        )
        return success_response(data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取安全库存预警失败")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 4. 齐套率改进建议 ====================


@router.get("/kitting/improvement-suggestions", summary="齐套率改进建议")
def get_improvement_suggestions(
    project_id: Optional[int] = Query(None, description="项目ID(可选)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    齐套率改进建议

    功能:
    - 瓶颈物料TOP10（频繁缺料分析）
    - 供应商交期分析（准时率、延迟天数、风险等级）
    - 建议提前采购的物料清单（长周期+库存不足）
    - 建议备库的通用物料（高频使用+多项目覆盖）
    - 齐套率改进目标及实施路径
    """
    try:
        svc = KittingOptimizationService(db)
        result = svc.get_improvement_suggestions(project_id=project_id)
        return success_response(data=result, message="齐套率改进建议生成成功")
    except Exception as e:
        logger.exception("生成改进建议失败")
        raise HTTPException(status_code=500, detail=str(e))
