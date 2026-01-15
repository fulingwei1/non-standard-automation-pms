# -*- coding: utf-8 -*-
"""
数据自动采集 API 端点
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.performance import PerformancePeriod
from app.services.performance_data_collector import PerformanceDataCollector
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/data-collection", tags=["数据采集"])


@router.get("/{engineer_id}", summary="获取数据采集结果")
async def get_data_collection(
    engineer_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师的数据采集结果"""
    collector = PerformanceDataCollector(db)

    # 获取周期日期
    if period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="考核周期不存在")
        start_date = period.start_date
        end_date = period.end_date
    elif not start_date or not end_date:
        # 使用当前周期
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="未找到当前考核周期")
        start_date = period.start_date
        end_date = period.end_date

    data = collector.collect_all_data(engineer_id, start_date, end_date)

    return ResponseModel(
        code=200,
        message="数据采集成功",
        data=data
    )


@router.get("/self-evaluation/{engineer_id}", summary="提取自我评价")
async def extract_self_evaluation(
    engineer_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从工作日志中提取自我评价数据"""
    collector = PerformanceDataCollector(db)

    if period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="考核周期不存在")
        start_date = period.start_date
        end_date = period.end_date
    elif not start_date or not end_date:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="未找到当前考核周期")
        start_date = period.start_date
        end_date = period.end_date

    result = collector.extract_self_evaluation_from_work_logs(
        engineer_id, start_date, end_date
    )

    return ResponseModel(
        code=200,
        message="自我评价提取成功",
        data=result
    )


@router.post("/collect-all/{engineer_id}", summary="触发完整数据采集")
async def trigger_collect_all(
    engineer_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """触发对指定工程师的完整数据采集（增强版：包含统计信息）"""
    collector = PerformanceDataCollector(db)

    period = db.query(PerformancePeriod).filter(
        PerformancePeriod.id == period_id
    ).first()
    if not period:
        raise HTTPException(status_code=404, detail="考核周期不存在")

    data = collector.collect_all_data(
        engineer_id, period.start_date, period.end_date
    )

    return ResponseModel(
        code=200,
        message="数据采集完成",
        data=data
    )


@router.get("/report/{engineer_id}", summary="生成数据采集报告")
async def generate_collection_report(
    engineer_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成数据采集报告（包含统计、缺失分析和建议）"""
    collector = PerformanceDataCollector(db)

    # 获取周期日期
    if period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="考核周期不存在")
        start_date = period.start_date
        end_date = period.end_date
    elif not start_date or not end_date:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="未找到当前考核周期")
        start_date = period.start_date
        end_date = period.end_date

    report = collector.generate_collection_report(
        engineer_id, start_date, end_date
    )

    return ResponseModel(
        code=200,
        message="数据采集报告生成成功",
        data=report
    )
