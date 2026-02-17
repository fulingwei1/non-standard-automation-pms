# -*- coding: utf-8 -*-
"""
EVM (Earned Value Management) 挣值管理 API端点

符合PMBOK标准的项目绩效测量API
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.auth import require_permission
from app.models import EarnedValueData, EarnedValueSnapshot, Project, User
from app.services.evm_service import EVMService
from app.utils.db_helpers import get_or_404

router = APIRouter()


# ==================== Pydantic Schemas ====================

class EVMDataCreate(BaseModel):
    """创建EVM数据的请求模型"""
    period_type: str = Field(..., description="周期类型：WEEK/MONTH/QUARTER")
    period_date: date = Field(..., description="周期截止日期")
    planned_value: Decimal = Field(..., ge=0, description="PV - 计划价值")
    earned_value: Decimal = Field(..., ge=0, description="EV - 挣得价值")
    actual_cost: Decimal = Field(..., ge=0, description="AC - 实际成本")
    budget_at_completion: Decimal = Field(..., gt=0, description="BAC - 完工预算")
    currency: str = Field(default="CNY", description="币种")
    notes: Optional[str] = Field(None, description="备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_type": "MONTH",
                "period_date": "2026-02-28",
                "planned_value": 500000.00,
                "earned_value": 450000.00,
                "actual_cost": 480000.00,
                "budget_at_completion": 2000000.00,
                "currency": "CNY",
                "notes": "2月份EVM数据"
            }
        }


class EVMDataResponse(BaseModel):
    """EVM数据响应模型"""
    id: int
    project_id: int
    project_code: Optional[str]
    period_type: str
    period_date: date
    period_label: Optional[str]
    
    # 核心三要素
    planned_value: Decimal
    earned_value: Decimal
    actual_cost: Decimal
    budget_at_completion: Decimal
    currency: str
    
    # 计算结果
    schedule_variance: Optional[Decimal]
    cost_variance: Optional[Decimal]
    schedule_performance_index: Optional[Decimal]
    cost_performance_index: Optional[Decimal]
    estimate_at_completion: Optional[Decimal]
    estimate_to_complete: Optional[Decimal]
    variance_at_completion: Optional[Decimal]
    to_complete_performance_index: Optional[Decimal]
    planned_percent_complete: Optional[Decimal]
    actual_percent_complete: Optional[Decimal]
    
    # 元数据
    data_source: str
    is_baseline: bool
    is_verified: bool
    created_at: date
    
    class Config:
        from_attributes = True


class EVMAnalysisResponse(BaseModel):
    """EVM综合分析响应"""
    project_id: int
    project_code: str
    project_name: str
    analysis_date: date
    
    # 最新EVM数据
    latest_data: Optional[EVMDataResponse]
    
    # 绩效分析
    performance_analysis: dict = Field(description="绩效分析结果")
    
    # 建议
    recommendations: List[str] = Field(description="改进建议")


class EVMTrendResponse(BaseModel):
    """EVM趋势数据响应"""
    project_id: int
    period_type: str
    data_points: List[EVMDataResponse]
    
    # 趋势摘要
    trend_summary: dict = Field(description="趋势摘要统计")


class EVMSnapshotCreate(BaseModel):
    """创建EVM快照的请求模型"""
    snapshot_name: Optional[str] = Field(None, description="快照名称")
    snapshot_type: str = Field(default="MONTHLY", description="快照类型")
    evm_data_id: Optional[int] = Field(None, description="关联的EVM数据ID")
    key_findings: Optional[str] = Field(None, description="关键发现")
    recommendations: Optional[str] = Field(None, description="改进建议")


# ==================== API Endpoints ====================

@router.get("/evm", response_model=EVMAnalysisResponse)
@require_permission("cost:read")
async def get_evm_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目EVM综合分析
    
    返回最新的EVM数据和绩效分析结果
    """
    # 获取项目
    project = get_or_404(db, Project, project_id, detail="项目不存在")
    
    # 获取EVM服务
    evm_service = EVMService(db)
    
    # 获取最新EVM数据
    latest_data = evm_service.get_latest_evm_data(project_id)
    
    if not latest_data:
        raise HTTPException(
            status_code=404,
            detail="该项目尚无EVM数据，请先记录EVM快照"
        )
    
    # 绩效分析
    performance_analysis = evm_service.analyze_performance(latest_data)
    
    # 生成建议
    recommendations = _generate_recommendations(latest_data, performance_analysis)
    
    return EVMAnalysisResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        analysis_date=date.today(),
        latest_data=EVMDataResponse.model_validate(latest_data),
        performance_analysis=performance_analysis,
        recommendations=recommendations
    )


@router.get("/evm/trend", response_model=EVMTrendResponse)
@require_permission("cost:read")
async def get_evm_trend(
    project_id: int,
    period_type: str = Query(default="MONTH", description="周期类型"),
    limit: int = Query(default=12, ge=1, le=24, description="返回数据点数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目EVM趋势数据
    
    用于绘制趋势图和历史分析
    """
    # 获取项目
    project = get_or_404(db, Project, project_id, detail="项目不存在")
    
    # 获取趋势数据
    evm_service = EVMService(db)
    trend_data = evm_service.get_evm_trend(project_id, period_type, limit)
    
    if not trend_data:
        raise HTTPException(
            status_code=404,
            detail="该项目尚无EVM趋势数据"
        )
    
    # 计算趋势摘要
    trend_summary = _calculate_trend_summary(trend_data)
    
    return EVMTrendResponse(
        project_id=project_id,
        period_type=period_type,
        data_points=[EVMDataResponse.model_validate(d) for d in trend_data],
        trend_summary=trend_summary
    )


@router.post("/evm/snapshot", response_model=EVMDataResponse)
@require_permission("cost:write")
async def create_evm_snapshot(
    project_id: int,
    evm_data: EVMDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    记录EVM快照
    
    创建新的EVM数据记录，系统会自动计算所有派生指标
    """
    # 检查项目是否存在
    project = get_or_404(db, Project, project_id, detail="项目不存在")
    
    # 检查是否已存在相同周期的数据
    existing = db.query(EarnedValueData).filter(
        EarnedValueData.project_id == project_id,
        EarnedValueData.period_type == evm_data.period_type,
        EarnedValueData.period_date == evm_data.period_date
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"该项目在 {evm_data.period_date} 的 {evm_data.period_type} 周期数据已存在"
        )
    
    # 创建EVM数据
    evm_service = EVMService(db)
    
    try:
        new_evm_data = evm_service.create_evm_data(
            project_id=project_id,
            period_type=evm_data.period_type,
            period_date=evm_data.period_date,
            pv=evm_data.planned_value,
            ev=evm_data.earned_value,
            ac=evm_data.actual_cost,
            bac=evm_data.budget_at_completion,
            currency=evm_data.currency,
            data_source="MANUAL",
            created_by=current_user.id,
            notes=evm_data.notes
        )
        
        return EVMDataResponse.model_validate(new_evm_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建EVM数据失败: {str(e)}")


@router.get("/evm/metrics", response_model=dict)
@require_permission("cost:read")
async def calculate_evm_metrics(
    pv: Decimal = Query(..., ge=0, description="计划价值"),
    ev: Decimal = Query(..., ge=0, description="挣得价值"),
    ac: Decimal = Query(..., ge=0, description="实际成本"),
    bac: Decimal = Query(..., gt=0, description="完工预算"),
):
    """
    EVM公式计算器（独立计算，不保存数据库）
    
    用于快速验证EVM公式或进行假设分析
    """
    from app.services.evm_service import EVMCalculator
    
    calculator = EVMCalculator()
    metrics = calculator.calculate_all_metrics(pv, ev, ac, bac)
    
    # 转换Decimal为float以便JSON序列化
    return {
        k: float(v) if v is not None else None
        for k, v in metrics.items()
    }


# ==================== Helper Functions ====================

def _generate_recommendations(evm_data: EarnedValueData, analysis: dict) -> List[str]:
    """根据EVM数据生成改进建议"""
    recommendations = []
    
    # 进度建议
    if analysis["schedule_status"] == "CRITICAL":
        recommendations.append("🚨 进度严重落后，建议：1) 增加资源投入 2) 优化工作流程 3) 重新评估项目计划")
    elif analysis["schedule_status"] == "WARNING":
        recommendations.append("⚠️ 进度轻微落后，建议密切监控关键路径任务，及时调整资源分配")
    
    # 成本建议
    if analysis["cost_status"] == "CRITICAL":
        recommendations.append("🚨 成本严重超支，建议：1) 立即审查成本结构 2) 削减非必要开支 3) 考虑范围变更")
    elif analysis["cost_status"] == "WARNING":
        recommendations.append("⚠️ 成本轻微超支，建议加强成本控制，审查采购和外协合同")
    
    # TCPI建议
    if evm_data.to_complete_performance_index:
        tcpi = float(evm_data.to_complete_performance_index)
        if tcpi > 1.2:
            recommendations.append(
                f"📊 TCPI={tcpi:.2f} > 1.2，完成剩余工作需要显著提高成本效率，目标较难达成"
            )
        elif tcpi > 1.0:
            recommendations.append(
                f"📊 TCPI={tcpi:.2f}，需要提高成本效率才能按预算完成项目"
            )
    
    # VAC建议
    if evm_data.variance_at_completion:
        vac = float(evm_data.variance_at_completion)
        if vac < 0:
            recommendations.append(
                f"💰 预计完工偏差 VAC={vac:,.2f}，项目预计超预算，建议申请预算变更"
            )
    
    if not recommendations:
        recommendations.append("✅ 项目整体表现良好，继续保持当前管理水平")
    
    return recommendations


def _calculate_trend_summary(trend_data: List[EarnedValueData]) -> dict:
    """计算趋势摘要统计"""
    if not trend_data:
        return {}
    
    # 最新和最早的数据点
    latest = trend_data[0]
    oldest = trend_data[-1]
    
    # SPI趋势
    latest_spi = float(latest.schedule_performance_index or 0)
    oldest_spi = float(oldest.schedule_performance_index or 0)
    spi_change = latest_spi - oldest_spi
    
    # CPI趋势
    latest_cpi = float(latest.cost_performance_index or 0)
    oldest_cpi = float(oldest.cost_performance_index or 0)
    cpi_change = latest_cpi - oldest_cpi
    
    # 趋势方向
    if spi_change > 0.05 and cpi_change > 0.05:
        trend_direction = "IMPROVING"
        trend_desc = "绩效持续改善"
    elif spi_change < -0.05 or cpi_change < -0.05:
        trend_direction = "DECLINING"
        trend_desc = "绩效下降，需要关注"
    else:
        trend_direction = "STABLE"
        trend_desc = "绩效保持稳定"
    
    return {
        "data_points_count": len(trend_data),
        "period_range": {
            "from": oldest.period_label,
            "to": latest.period_label
        },
        "spi_trend": {
            "latest": latest_spi,
            "oldest": oldest_spi,
            "change": spi_change,
            "direction": "UP" if spi_change > 0 else "DOWN" if spi_change < 0 else "FLAT"
        },
        "cpi_trend": {
            "latest": latest_cpi,
            "oldest": oldest_cpi,
            "change": cpi_change,
            "direction": "UP" if cpi_change > 0 else "DOWN" if cpi_change < 0 else "FLAT"
        },
        "overall_trend": {
            "direction": trend_direction,
            "description": trend_desc
        }
    }
