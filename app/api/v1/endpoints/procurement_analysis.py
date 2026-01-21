# -*- coding: utf-8 -*-
"""
采购分析 API endpoints
提供采购成本趋势、物料价格波动、供应商交期准时率等分析
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
# from app.services.procurement_analysis_service import procurement_analysis_service  # TODO: Service file doesn't exist

router = APIRouter()


# ==================== 采购成本趋势分析 ====================


@router.get("/cost-trend", response_model=ResponseModel)
def get_procurement_cost_trend(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: str = Query("month", description="分组方式: month/quarter/year"),
    category_id: Optional[int] = Query(None, description="物料分类筛选"),
    project_id: Optional[int] = Query(None, description="项目筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    采购成本趋势分析

    - 按月度/季度/年度聚合采购金额
    - 计算环比增长率
    - 支持按物料分类、项目筛选
    """
    # 设置默认时间范围：最近6个月
    if not start_date:
        start_date = date.today() - timedelta(days=180)
    if not end_date:
        end_date = date.today()

    data = procurement_analysis_service.get_cost_trend_data(
        db=db,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
        category_id=category_id,
        project_id=project_id,
    )

    return ResponseModel(code=200, message="success", data=data)


# ==================== 物料价格波动监控 ====================


@router.get("/price-fluctuation", response_model=ResponseModel)
def get_material_price_fluctuation(
    *,
    db: Session = Depends(deps.get_db),
    material_code: Optional[str] = Query(None, description="物料编码"),
    category_id: Optional[int] = Query(None, description="物料分类"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, description="返回物料数量限制", ge=1, le=100),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    物料价格波动监控

    - 同一物料不同时间点的价格对比
    - 同一物料不同供应商的价格对比
    - 价格波动率计算
    """
    # 设置默认时间范围：最近1年
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()

    data = procurement_analysis_service.get_price_fluctuation_data(
        db=db,
        material_code=material_code,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return ResponseModel(code=200, message="success", data=data)


# ==================== 供应商交期准时率 ====================


@router.get("/delivery-performance", response_model=ResponseModel)
def get_supplier_delivery_performance(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    供应商交期准时率

    - 对比承诺交期和实际收货日期
    - 按供应商统计准时率
    - 延期订单详情
    """
    # 设置默认时间范围：最近6个月
    if not start_date:
        start_date = date.today() - timedelta(days=180)
    if not end_date:
        end_date = date.today()

    data = procurement_analysis_service.get_delivery_performance_data(
        db=db, start_date=start_date, end_date=end_date, supplier_id=supplier_id
    )

    return ResponseModel(code=200, message="success", data=data)


# ==================== 采购申请处理时效 ====================


@router.get("/request-efficiency", response_model=ResponseModel)
def get_procurement_request_efficiency(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    采购申请处理时效

    - 申请提交到订单创建的时间差
    - 平均处理时长统计
    - 超时未处理申请统计
    """
    # 设置默认时间范围：最近3个月
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    data = procurement_analysis_service.get_request_efficiency_data(
        db=db, start_date=start_date, end_date=end_date
    )

    return ResponseModel(code=200, message="success", data=data)


# ==================== 物料质量合格率统计 ====================


@router.get("/quality-rate", response_model=ResponseModel)
def get_material_quality_rate(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    物料质量合格率统计

    - 按供应商、物料统计合格率
    - 合格数量 / (合格数量 + 不合格数量)
    - 供应商质量排名
    """
    # 设置默认时间范围：最近6个月
    if not start_date:
        start_date = date.today() - timedelta(days=180)
    if not end_date:
        end_date = date.today()

    data = procurement_analysis_service.get_quality_rate_data(
        db=db, start_date=start_date, end_date=end_date, supplier_id=supplier_id
    )

    return ResponseModel(code=200, message="success", data=data)


# ==================== 采购分析概览 ====================


@router.get("/overview", response_model=ResponseModel)
def get_procurement_overview(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    采购分析概览

    返回各分析模块的汇总数据，用于仪表盘展示
    """
    today = date.today()
    last_month = today - timedelta(days=30)
    last_quarter = today - timedelta(days=90)

    # 并行获取各模块数据
    cost_trend = procurement_analysis_service.get_cost_trend_data(
        db=db, start_date=last_quarter, end_date=today, group_by="month"
    )

    delivery_performance = procurement_analysis_service.get_delivery_performance_data(
        db=db, start_date=last_quarter, end_date=today
    )

    quality_rate = procurement_analysis_service.get_quality_rate_data(
        db=db, start_date=last_quarter, end_date=today
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "procurement_summary": {
                "quarter_amount": cost_trend["summary"]["total_amount"],
                "quarter_orders": cost_trend["summary"]["total_orders"],
                "avg_on_time_rate": delivery_performance["summary"]["avg_on_time_rate"],
                "avg_quality_rate": quality_rate["summary"]["avg_pass_rate"],
                "delayed_orders_count": delivery_performance["summary"][
                    "total_delayed_orders"
                ],
            },
            "period": {
                "start_date": last_quarter.isoformat(),
                "end_date": today.isoformat(),
            },
        },
    )
