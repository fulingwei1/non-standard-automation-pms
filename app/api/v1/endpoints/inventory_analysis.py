# -*- coding: utf-8 -*-
"""
库存分析 API endpoints
提供库存周转率、呆滞物料预警、安全库存达标率等分析
"""

from typing import Any, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.inventory_analysis_service import inventory_analysis_service

router = APIRouter()


# ==================== 库存周转率分析 ====================

@router.get("/turnover-rate", response_model=ResponseModel)
def get_inventory_turnover_rate(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    category_id: Optional[int] = Query(None, description="物料分类筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    库存周转率分析

    - 周转率 = 本期消耗金额 / 平均库存价值
    - 周转天数 = 365 / 周转率
    - 按物料分类统计周转率
    """
    # 设置默认时间范围：最近1年
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()

    data = inventory_analysis_service.get_turnover_rate_data(
        db=db,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id
    )

    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


# ==================== 呆滞物料预警 ====================

@router.get("/stale-materials", response_model=ResponseModel)
def get_stale_materials(
    *,
    db: Session = Depends(deps.get_db),
    threshold_days: int = Query(90, description="无出入库记录天数阈值", ge=30, le=365),
    category_id: Optional[int] = Query(None, description="物料分类筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    呆滞物料预警

    - 库存 > 0 且 N 天无变动
    - 按库龄分组统计
    - 呆滞物料金额统计
    """
    data = inventory_analysis_service.get_stale_materials_data(
        db=db,
        threshold_days=threshold_days,
        category_id=category_id
    )

    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


# ==================== 安全库存达标率 ====================

@router.get("/safety-stock-compliance", response_model=ResponseModel)
def get_safety_stock_compliance(
    *,
    db: Session = Depends(deps.get_db),
    category_id: Optional[int] = Query(None, description="物料分类筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    安全库存达标率

    - current_stock >= safety_stock 的物料占比
    - 缺货物料列表
    - 低库存预警
    """
    data = inventory_analysis_service.get_safety_stock_compliance_data(
        db=db,
        category_id=category_id
    )

    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


# ==================== 物料ABC分类分析 ====================

@router.get("/abc-analysis", response_model=ResponseModel)
def get_abc_analysis(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="分析开始日期"),
    end_date: Optional[date] = Query(None, description="分析结束日期"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    物料ABC分类分析

    - 按采购金额累计占比分类
    - A类: 70%, B类: 20%, C类: 10%
    - ABC分类统计和物料列表
    """
    # 设置默认时间范围：最近1年
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()

    data = inventory_analysis_service.get_abc_analysis_data(
        db=db,
        start_date=start_date,
        end_date=end_date
    )

    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


# ==================== 库存成本占用分析 ====================

@router.get("/cost-occupancy", response_model=ResponseModel)
def get_inventory_cost_occupancy(
    *,
    db: Session = Depends(deps.get_db),
    category_id: Optional[int] = Query(None, description="物料分类筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    库存成本占用分析

    - 各类别物料的库存金额占比
    - 按物料分类统计库存价值
    - 高库存占用物料TOP榜
    """
    data = inventory_analysis_service.get_cost_occupancy_data(
        db=db,
        category_id=category_id
    )

    return ResponseModel(
        code=200,
        message="success",
        data=data
    )


# ==================== 库存分析概览 ====================

@router.get("/overview", response_model=ResponseModel)
def get_inventory_overview(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    库存分析概览

    返回各分析模块的汇总数据，用于仪表盘展示
    """
    today = date.today()
    last_quarter = today - timedelta(days=90)

    # 获取各模块数据
    stale_materials = inventory_analysis_service.get_stale_materials_data(
        db=db, threshold_days=90
    )

    safety_stock = inventory_analysis_service.get_safety_stock_compliance_data(
        db=db
    )

    cost_occupancy = inventory_analysis_service.get_cost_occupancy_data(
        db=db
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "inventory_summary": {
                "total_inventory_value": cost_occupancy['summary']['total_inventory_value'],
                "stale_materials_count": stale_materials['summary']['stale_count'],
                "stale_materials_value": stale_materials['summary']['stale_value'],
                "safety_stock_compliance_rate": safety_stock['summary']['compliant_rate'],
                "warning_count": safety_stock['summary']['warning'],
                "out_of_stock_count": safety_stock['summary']['out_of_stock']
            },
            "period": {
                "as_of_date": today.isoformat()
            }
        }
    )
