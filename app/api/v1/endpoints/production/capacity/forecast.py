# -*- coding: utf-8 -*-
"""
产能预测接口
基于历史数据的线性回归,考虑季节性因素
"""
from datetime import date, timedelta
from typing import List, Optional
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    WorkerEfficiencyRecord,
)

router = APIRouter()


@router.get("/forecast")
async def forecast_capacity(
    type: str = Query("equipment", description="类型: equipment/worker"),
    equipment_id: Optional[int] = Query(None, description="设备ID(type=equipment时)"),
    worker_id: Optional[int] = Query(None, description="工人ID(type=worker时)"),
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    history_days: int = Query(90, ge=30, le=365, description="历史数据天数"),
    forecast_days: int = Query(30, ge=7, le=90, description="预测天数"),
    db: Session = Depends(get_db),
):
    """
    产能预测
    
    预测方法:
    1. 基于历史数据的线性回归
    2. 考虑季节性因素(周期性波动)
    3. 趋势外推
    
    返回预测值和置信区间
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=history_days)
    
    if type == "equipment":
        # 设备产能预测
        filters = [
            EquipmentOEERecord.record_date >= start_date,
            EquipmentOEERecord.record_date <= end_date,
        ]
        if equipment_id:
            filters.append(EquipmentOEERecord.equipment_id == equipment_id)
        if workshop_id:
            filters.append(EquipmentOEERecord.workshop_id == workshop_id)
        
        # 获取历史数据
        historical_data = (
            db.query(
                EquipmentOEERecord.record_date,
                func.sum(EquipmentOEERecord.actual_output).label('daily_output'),
                func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                func.sum(EquipmentOEERecord.operating_time).label('operating_time'),
            )
            .filter(and_(*filters))
            .group_by(EquipmentOEERecord.record_date)
            .order_by(EquipmentOEERecord.record_date)
            .all()
        )
        
        if not historical_data or len(historical_data) < 7:
            return {
                "code": 400,
                "message": "历史数据不足,无法进行预测(至少需要7天数据)",
                "data": None,
            }
        
        # 计算预测
        forecast_result = _calculate_forecast(
            historical_data,
            forecast_days,
            value_field='daily_output'
        )
        
        # 计算产能趋势
        recent_avg = sum(row.daily_output for row in historical_data[-7:]) / 7
        overall_avg = sum(row.daily_output for row in historical_data) / len(historical_data)
        trend = "上升" if recent_avg > overall_avg * 1.05 else ("下降" if recent_avg < overall_avg * 0.95 else "平稳")
        
        return {
            "code": 200,
            "message": "预测成功",
            "data": {
                "type": "equipment",
                "equipment_id": equipment_id,
                "workshop_id": workshop_id,
                "history_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": history_days,
                },
                "historical_summary": {
                    "total_output": sum(row.daily_output for row in historical_data),
                    "avg_daily_output": sum(row.daily_output for row in historical_data) / len(historical_data),
                    "avg_oee": sum(row.avg_oee for row in historical_data) / len(historical_data),
                    "trend": trend,
                },
                "forecast": forecast_result,
            },
        }
        
    elif type == "worker":
        # 工人效率预测
        filters = [
            WorkerEfficiencyRecord.record_date >= start_date,
            WorkerEfficiencyRecord.record_date <= end_date,
        ]
        if worker_id:
            filters.append(WorkerEfficiencyRecord.worker_id == worker_id)
        if workshop_id:
            filters.append(WorkerEfficiencyRecord.workshop_id == workshop_id)
        
        # 获取历史数据
        historical_data = (
            db.query(
                WorkerEfficiencyRecord.record_date,
                func.avg(WorkerEfficiencyRecord.efficiency).label('daily_efficiency'),
                func.sum(WorkerEfficiencyRecord.completed_qty).label('daily_output'),
            )
            .filter(and_(*filters))
            .group_by(WorkerEfficiencyRecord.record_date)
            .order_by(WorkerEfficiencyRecord.record_date)
            .all()
        )
        
        if not historical_data or len(historical_data) < 7:
            return {
                "code": 400,
                "message": "历史数据不足,无法进行预测(至少需要7天数据)",
                "data": None,
            }
        
        # 计算预测
        efficiency_forecast = _calculate_forecast(
            historical_data,
            forecast_days,
            value_field='daily_efficiency'
        )
        
        output_forecast = _calculate_forecast(
            historical_data,
            forecast_days,
            value_field='daily_output'
        )
        
        return {
            "code": 200,
            "message": "预测成功",
            "data": {
                "type": "worker",
                "worker_id": worker_id,
                "workshop_id": workshop_id,
                "history_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": history_days,
                },
                "historical_summary": {
                    "avg_efficiency": sum(row.daily_efficiency for row in historical_data) / len(historical_data),
                    "total_output": sum(row.daily_output for row in historical_data),
                },
                "efficiency_forecast": efficiency_forecast,
                "output_forecast": output_forecast,
            },
        }
    
    else:
        return {
            "code": 400,
            "message": "不支持的类型",
            "data": None,
        }


def _calculate_forecast(historical_data, forecast_days: int, value_field: str):
    """
    计算预测值
    使用简单线性回归 + 移动平均
    """
    n = len(historical_data)
    
    # 提取数据
    values = [float(getattr(row, value_field)) for row in historical_data]
    
    # 计算线性回归参数
    x_values = list(range(n))
    x_mean = sum(x_values) / n
    y_mean = sum(values) / n
    
    # 计算斜率和截距
    numerator = sum((x - x_mean) * (values[i] - y_mean) for i, x in enumerate(x_values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
    
    intercept = y_mean - slope * x_mean
    
    # 计算季节性因子(7天周期)
    weekly_pattern = [0] * 7
    weekly_counts = [0] * 7
    
    for i, row in enumerate(historical_data):
        day_of_week = row.record_date.weekday()
        weekly_pattern[day_of_week] += values[i]
        weekly_counts[day_of_week] += 1
    
    # 平均每周模式
    for i in range(7):
        if weekly_counts[i] > 0:
            weekly_pattern[i] = weekly_pattern[i] / weekly_counts[i]
        else:
            weekly_pattern[i] = y_mean
    
    weekly_avg = sum(weekly_pattern) / 7
    # 季节性因子(相对于平均值)
    seasonal_factors = [p / weekly_avg if weekly_avg > 0 else 1.0 for p in weekly_pattern]
    
    # 计算标准差(用于置信区间)
    residuals = [values[i] - (slope * i + intercept) for i in range(n)]
    variance = sum(r ** 2 for r in residuals) / n
    std_dev = math.sqrt(variance)
    
    # 生成预测
    forecast_values = []
    base_date = historical_data[-1].record_date
    
    for day in range(1, forecast_days + 1):
        forecast_date = base_date + timedelta(days=day)
        
        # 线性趋势值
        trend_value = slope * (n + day - 1) + intercept
        
        # 应用季节性因子
        day_of_week = forecast_date.weekday()
        seasonal_factor = seasonal_factors[day_of_week]
        forecast_value = trend_value * seasonal_factor
        
        # 置信区间(95% ≈ 1.96 * std_dev)
        confidence_interval = 1.96 * std_dev
        
        forecast_values.append({
            "date": forecast_date.isoformat(),
            "forecast_value": round(max(0, forecast_value), 2),
            "lower_bound": round(max(0, forecast_value - confidence_interval), 2),
            "upper_bound": round(forecast_value + confidence_interval, 2),
            "confidence": "95%",
        })
    
    # 计算预测汇总
    total_forecast = sum(item['forecast_value'] for item in forecast_values)
    avg_forecast = total_forecast / len(forecast_values)
    
    return {
        "forecast_days": forecast_days,
        "forecast_values": forecast_values,
        "summary": {
            "total_forecast": round(total_forecast, 2),
            "avg_daily_forecast": round(avg_forecast, 2),
            "trend_slope": round(slope, 4),
            "confidence_level": "95%",
        },
        "model_info": {
            "method": "线性回归 + 季节性调整",
            "r_squared": round(_calculate_r_squared(values, slope, intercept), 4),
            "std_dev": round(std_dev, 2),
        },
    }


def _calculate_r_squared(values, slope, intercept):
    """计算R²(拟合优度)"""
    n = len(values)
    y_mean = sum(values) / n
    
    # 总平方和
    ss_tot = sum((y - y_mean) ** 2 for y in values)
    
    # 残差平方和
    ss_res = sum((values[i] - (slope * i + intercept)) ** 2 for i in range(n))
    
    # R²
    if ss_tot == 0:
        return 0
    
    r_squared = 1 - (ss_res / ss_tot)
    return max(0, min(1, r_squared))  # 限制在0-1之间
