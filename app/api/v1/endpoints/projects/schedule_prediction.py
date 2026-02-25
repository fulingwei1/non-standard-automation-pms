# -*- coding: utf-8 -*-
"""
项目进度预测API端点
Project Schedule Prediction Endpoints
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api import deps
from app.core import security
from app.core.schemas import success_response
from app.models.user import User
from app.services.schedule_prediction_service import SchedulePredictionService

router = APIRouter()


# ==================== Pydantic Schemas ====================

class PredictionRequest(BaseModel):
    """预测请求模型"""
    current_progress: float = Field(..., ge=0, le=100, description="当前进度 (%)")
    planned_progress: float = Field(..., ge=0, le=100, description="计划进度 (%)")
    remaining_days: int = Field(..., ge=0, description="剩余天数")
    team_size: int = Field(..., ge=1, description="团队规模（人数）")
    use_ai: bool = Field(True, description="是否使用AI模型预测")
    include_solutions: bool = Field(False, description="是否生成赶工方案")
    project_data: Optional[dict] = Field(None, description="项目详细数据")


class PredictionResponse(BaseModel):
    """预测响应模型"""
    prediction_id: int
    project_id: int
    current_progress: float
    planned_progress: float
    prediction: dict
    features: dict
    details: Optional[dict] = None
    catch_up_solutions: Optional[List[dict]] = None


class AlertQueryParams(BaseModel):
    """预警查询参数"""
    severity: Optional[str] = Field(None, description="严重程度: low/medium/high/critical")
    unread_only: bool = Field(False, description="仅未读")
    limit: int = Field(20, ge=1, le=100, description="返回数量")


class ReportRequest(BaseModel):
    """报告生成请求"""
    report_type: str = Field("weekly", description="报告类型: weekly/monthly/custom")
    include_recommendations: bool = Field(True, description="包含建议")


class SolutionApprovalRequest(BaseModel):
    """方案审批请求"""
    approved: bool = Field(..., description="是否批准")
    comment: Optional[str] = Field(None, description="审批意见")


# ==================== API Endpoints ====================

@router.post("/predict")
def predict_completion_date(
    project_id: int,
    request: PredictionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    预测项目完成日期
    
    ## 功能
    - 基于当前进度和历史数据预测项目完成日期
    - 可选择使用AI模型或简单线性预测
    - 自动评估延期风险和置信度
    - 可选生成赶工方案
    
    ## 返回
    - 预测完成日期
    - 预计延期天数
    - 置信度
    - 风险等级
    - （可选）赶工方案列表
    """
    try:
        service = SchedulePredictionService(db)
        
        # 执行预测
        result = service.predict_completion_date(
            project_id=project_id,
            current_progress=request.current_progress,
            planned_progress=request.planned_progress,
            remaining_days=request.remaining_days,
            team_size=request.team_size,
            project_data=request.project_data,
            use_ai=request.use_ai,
        )
        
        # 如果需要生成赶工方案
        if request.include_solutions:
            delay_days = result["prediction"]["delay_days"]
            if delay_days > 0:  # 只有延期时才生成方案
                solutions = service.generate_catch_up_solutions(
                    project_id=project_id,
                    prediction_id=result["prediction_id"],
                    delay_days=delay_days,
                    project_data=request.project_data,
                )
                result["catch_up_solutions"] = solutions
        
        # 创建预警（如果需要）
        delay_days = result["prediction"]["delay_days"]
        progress_deviation = request.current_progress - request.planned_progress
        
        if delay_days >= 3 or abs(progress_deviation) >= 10:
            service.check_and_create_alerts(
                project_id=project_id,
                prediction_id=result["prediction_id"],
                delay_days=delay_days,
                progress_deviation=progress_deviation,
                project_data=request.project_data,
            )
        
        return success_response(
            data=result,
            message="预测完成"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.get("/alerts")
def get_project_alerts(
    project_id: int,
    severity: Optional[str] = Query(None, description="严重程度过滤"),
    unread_only: bool = Query(False, description="仅未读预警"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目预警列表
    
    ## 功能
    - 查询项目的进度预警记录
    - 支持按严重程度过滤
    - 支持仅查看未读预警
    
    ## 返回
    - 预警列表
    - 总数
    - 未读数量
    """
    try:
        service = SchedulePredictionService(db)
        
        alerts = service.get_project_alerts(
            project_id=project_id,
            severity=severity,
            unread_only=unread_only,
            limit=limit,
        )
        
        # 统计
        from app.models.project.schedule_prediction import ScheduleAlert
        total = db.query(ScheduleAlert).filter(
            ScheduleAlert.project_id == project_id
        ).count()
        
        unread_count = db.query(ScheduleAlert).filter(
            ScheduleAlert.project_id == project_id,
            ScheduleAlert.is_read == False
        ).count()
        
        return success_response(
            data={
                "alerts": alerts,
                "total": total,
                "unread_count": unread_count,
            },
            message="获取预警列表成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预警失败: {str(e)}")


@router.put("/alerts/{alert_id}/read")
def mark_alert_as_read(
    project_id: int,
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """标记预警为已读"""
    from app.models.project.schedule_prediction import ScheduleAlert
    
    alert = db.query(ScheduleAlert).filter(
        ScheduleAlert.id == alert_id,
        ScheduleAlert.project_id == project_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")
    
    alert.is_read = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now()
    
    db.commit()
    
    return success_response(message="已标记为已读")


@router.get("/solutions")
def get_catch_up_solutions(
    project_id: int,
    status: Optional[str] = Query(None, description="方案状态过滤"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目赶工方案列表
    
    ## 功能
    - 查询项目的所有赶工方案
    - 支持按状态过滤
    
    ## 返回
    - 方案列表（包含详细评估信息）
    """
    from app.models.project.schedule_prediction import CatchUpSolution
    
    query = db.query(CatchUpSolution).filter(
        CatchUpSolution.project_id == project_id
    )
    
    if status:
        query = query.filter(CatchUpSolution.status == status)
    
    solutions = query.order_by(
        CatchUpSolution.is_recommended.desc(),
        CatchUpSolution.created_at.desc()
    ).all()
    
    result = [
        {
            "id": sol.id,
            "name": sol.solution_name,
            "type": sol.solution_type,
            "description": sol.description,
            "actions": sol.actions,
            "estimated_catch_up_days": sol.estimated_catch_up_days,
            "additional_cost": float(sol.additional_cost) if sol.additional_cost else 0,
            "risk_level": sol.risk_level,
            "success_rate": float(sol.success_rate) if sol.success_rate else 0,
            "status": sol.status,
            "is_recommended": sol.is_recommended,
            "evaluation": sol.evaluation_details,
            "created_at": sol.created_at.isoformat(),
        }
        for sol in solutions
    ]
    
    return success_response(
        data=result,
        message="获取方案列表成功"
    )


@router.post("/solutions/{solution_id}/approve")
def approve_solution(
    project_id: int,
    solution_id: int,
    request: SolutionApprovalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批赶工方案
    
    ## 功能
    - 批准或拒绝赶工方案
    - 记录审批人和意见
    """
    from datetime import datetime
    from app.models.project.schedule_prediction import CatchUpSolution
    
    solution = db.query(CatchUpSolution).filter(
        CatchUpSolution.id == solution_id,
        CatchUpSolution.project_id == project_id
    ).first()
    
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    if solution.status != "pending":
        raise HTTPException(status_code=400, detail="方案已审批，无法重复操作")
    
    # 更新状态
    solution.status = "approved" if request.approved else "rejected"
    solution.approved_by = current_user.id
    solution.approved_at = datetime.now()
    solution.approval_comment = request.comment
    
    db.commit()
    
    return success_response(
        message=f"方案已{'批准' if request.approved else '拒绝'}"
    )


@router.post("/report")
def generate_schedule_report(
    project_id: int,
    request: ReportRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成进度分析报告
    
    ## 功能
    - 生成项目进度分析报告
    - 包含进度概览、延期分析、风险预测
    - 可选包含AI生成的改进建议
    
    ## 返回
    - 报告ID
    - 报告摘要
    - 下载链接
    """
    try:
        from app.models.project.schedule_prediction import ProjectSchedulePrediction
        from sqlalchemy import desc
        
        # 获取最近的预测记录
        latest_prediction = db.query(ProjectSchedulePrediction).filter(
            ProjectSchedulePrediction.project_id == project_id
        ).order_by(desc(ProjectSchedulePrediction.prediction_date)).first()
        
        if not latest_prediction:
            raise HTTPException(status_code=404, detail="暂无预测数据")
        
        # 构建报告摘要
        report_summary = {
            "on_track": (latest_prediction.delay_days or 0) <= 0,
            "delay_days": latest_prediction.delay_days or 0,
            "risk_level": latest_prediction.risk_level,
            "confidence": float(latest_prediction.confidence) if latest_prediction.confidence else 0,
        }
        
        # 这里简化处理，实际应该生成PDF文件
        report_data = {
            "report_id": latest_prediction.id,
            "summary": report_summary,
            "file_url": f"/reports/project-{project_id}-schedule-{latest_prediction.id}.pdf",
            "generated_at": datetime.now().isoformat(),
        }
        
        return success_response(
            data=report_data,
            message="报告生成成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.get("/risk-overview")
def get_risk_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取所有项目风险概览
    
    ## 功能
    - 批量检查所有项目的延期风险
    - 统计风险项目数量
    - 返回高风险项目列表
    
    ## 返回
    - 总项目数
    - 风险项目数
    - 严重风险项目数
    - 高风险项目列表
    """
    try:
        service = SchedulePredictionService(db)
        overview = service.get_risk_overview()
        
        return success_response(
            data=overview,
            message="获取风险概览成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险概览失败: {str(e)}")


@router.get("/predictions/history")
def get_prediction_history(
    project_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目历史预测记录
    
    ## 功能
    - 查看项目的历史预测数据
    - 用于分析预测准确性和趋势
    
    ## 返回
    - 历史预测记录列表
    """
    from app.models.project.schedule_prediction import ProjectSchedulePrediction
    from sqlalchemy import desc
    
    predictions = db.query(ProjectSchedulePrediction).filter(
        ProjectSchedulePrediction.project_id == project_id
    ).order_by(desc(ProjectSchedulePrediction.prediction_date)).limit(limit).all()
    
    result = [
        {
            "id": pred.id,
            "prediction_date": pred.prediction_date.isoformat(),
            "predicted_completion_date": str(pred.predicted_completion_date) if pred.predicted_completion_date else None,
            "delay_days": pred.delay_days,
            "confidence": float(pred.confidence) if pred.confidence else 0,
            "risk_level": pred.risk_level,
            "model_version": pred.model_version,
        }
        for pred in predictions
    ]
    
    return success_response(
        data=result,
        message="获取历史预测成功"
    )


# 导入datetime
from datetime import datetime
