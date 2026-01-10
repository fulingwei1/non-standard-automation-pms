# -*- coding: utf-8 -*-
"""
售前系统集成 API
处理与 presales-evaluation-system 的数据对接，包括：
- 线索评估通过后自动创建项目
- 中标率预测
- 资源浪费分析
- 销售人员绩效分析
"""

from typing import Any, List, Optional, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project, Customer, Machine
from app.models.enums import (
    ProjectStageEnum, ProjectHealthEnum, MachineStatusEnum,
    PresalesLeadStatusEnum, EvaluationDecisionEnum, WinProbabilityLevelEnum,
    LeadOutcomeEnum, LossReasonEnum
)
from app.schemas.presales import (
    LeadConversionRequest, LeadConversionResponse,
    WinRatePredictionRequest, WinRatePredictionResponse,
    ResourceInvestmentSummary, ResourceWasteAnalysis,
    SalespersonPerformance, SalespersonRanking,
    FailureCaseAnalysis, FailurePatternAnalysis,
    PresalesDashboardData, DimensionScore
)
from app.schemas.common import ResponseModel

router = APIRouter()


# ==================== 线索转项目 ====================

def convert_lead_code_to_project_code(lead_id: str) -> str:
    """将线索编号转换为项目编号

    XS2501001 -> PJ2501001
    """
    if lead_id.upper().startswith('XS'):
        return 'PJ' + lead_id[2:]
    return 'PJ' + lead_id


@router.post("/from-lead", response_model=ResponseModel[LeadConversionResponse])
async def create_project_from_lead(
    lead_data: LeadConversionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """从评估通过的销售线索创建项目

    由 presales-evaluation-system 在评估通过后调用
    """
    # 验证评估决策
    if lead_data.decision != EvaluationDecisionEnum.APPROVED.value:
        return ResponseModel(
            code=400,
            message=f"线索评估未通过，当前决策: {lead_data.decision}",
            data=LeadConversionResponse(
                success=False,
                lead_id=lead_data.lead_id,
                message=f"评估未通过: {lead_data.decision}"
            )
        )

    # 生成项目编号
    project_code = convert_lead_code_to_project_code(lead_data.lead_id)

    # 检查是否已存在该项目
    existing_project = db.query(Project).filter(Project.project_code == project_code).first()
    if existing_project:
        return ResponseModel(
            code=400,
            message=f"项目 {project_code} 已存在",
            data=LeadConversionResponse(
                success=False,
                project_id=existing_project.id,
                project_code=project_code,
                lead_id=lead_data.lead_id,
                message=f"项目已存在，ID: {existing_project.id}"
            )
        )

    # 查找或创建客户
    customer = db.query(Customer).filter(Customer.name == lead_data.customer_name).first()
    if not customer:
        customer = Customer(
            name=lead_data.customer_name,
            industry=lead_data.customer_industry,
            contact_name=lead_data.customer_contact,
            contact_phone=lead_data.customer_phone,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(customer)
        db.flush()

    # 创建项目（S0 售前跟进阶段）
    project = Project(
        project_code=project_code,
        name=lead_data.lead_name,
        customer_id=customer.id,
        salesperson_id=lead_data.salesperson_id,
        current_stage=ProjectStageEnum.S0,  # 新增的售前跟进阶段
        health_status=ProjectHealthEnum.H1,
        contract_amount=lead_data.estimated_amount,
        expected_delivery_date=lead_data.expected_delivery_date,
        machine_count=lead_data.machine_count,
        description=lead_data.requirement_summary,
        is_active=True,
        created_at=datetime.utcnow(),
        created_by=current_user.id,
        # 存储评估信息（扩展字段）
        evaluation_score=lead_data.evaluation_score,
        predicted_win_rate=lead_data.predicted_win_rate,
        source_lead_id=lead_data.lead_id,  # 关联原线索
    )

    db.add(project)
    db.flush()

    # 如果有设备数量，创建设备记录
    for i in range(lead_data.machine_count):
        machine = Machine(
            project_id=project.id,
            machine_code=f"M{str(i+1).zfill(3)}",
            name=f"{lead_data.lead_name}-设备{i+1}",
            status=MachineStatusEnum.PLANNING,
            created_at=datetime.utcnow()
        )
        db.add(machine)

    db.commit()

    return ResponseModel(
        code=200,
        message="项目创建成功",
        data=LeadConversionResponse(
            success=True,
            project_id=project.id,
            project_code=project_code,
            lead_id=lead_data.lead_id,
            message=f"已从线索 {lead_data.lead_id} 创建项目 {project_code}"
        )
    )


# ==================== 中标率预测 ====================

def calculate_win_rate(
    dimension_scores: DimensionScore,
    salesperson_win_rate: float,
    customer_cooperation_count: int,
    competitor_count: int = 3,
    is_repeat_customer: bool = False
) -> tuple[float, str, Dict[str, Any]]:
    """计算中标率预测

    返回: (预测中标率, 概率等级, 影响因素)
    """
    # 1. 基础分数（五维评估加权）
    base_score = dimension_scores.total_score / 100  # 转换为0-1

    # 2. 销售人员历史中标率调整
    salesperson_factor = 0.5 + salesperson_win_rate * 0.5

    # 3. 客户关系调整
    customer_factor = 1.0
    if customer_cooperation_count > 5:
        customer_factor = 1.3
    elif customer_cooperation_count > 3:
        customer_factor = 1.2
    elif customer_cooperation_count > 1:
        customer_factor = 1.1
    elif is_repeat_customer:
        customer_factor = 1.05

    # 4. 竞争对手调整
    competitor_factor = 1.0
    if competitor_count <= 1:
        competitor_factor = 1.2
    elif competitor_count <= 3:
        competitor_factor = 1.0
    elif competitor_count <= 5:
        competitor_factor = 0.85
    else:
        competitor_factor = 0.7

    # 5. 综合计算
    predicted_rate = base_score * salesperson_factor * customer_factor * competitor_factor
    predicted_rate = min(max(predicted_rate, 0), 1)  # 限制在0-1范围

    # 6. 确定概率等级
    if predicted_rate >= 0.8:
        level = WinProbabilityLevelEnum.VERY_HIGH.value
    elif predicted_rate >= 0.6:
        level = WinProbabilityLevelEnum.HIGH.value
    elif predicted_rate >= 0.4:
        level = WinProbabilityLevelEnum.MEDIUM.value
    elif predicted_rate >= 0.2:
        level = WinProbabilityLevelEnum.LOW.value
    else:
        level = WinProbabilityLevelEnum.VERY_LOW.value

    # 7. 影响因素分析
    factors = {
        "base_score": round(base_score, 3),
        "salesperson_factor": round(salesperson_factor, 3),
        "salesperson_win_rate": round(salesperson_win_rate, 3),
        "customer_factor": round(customer_factor, 3),
        "customer_cooperation_count": customer_cooperation_count,
        "competitor_factor": round(competitor_factor, 3),
        "competitor_count": competitor_count,
        "dimension_scores": {
            "requirement_maturity": dimension_scores.requirement_maturity,
            "technical_feasibility": dimension_scores.technical_feasibility,
            "business_feasibility": dimension_scores.business_feasibility,
            "delivery_risk": dimension_scores.delivery_risk,
            "customer_relationship": dimension_scores.customer_relationship
        }
    }

    return predicted_rate, level, factors


def get_win_rate_recommendations(
    predicted_rate: float,
    factors: Dict[str, Any]
) -> List[str]:
    """根据预测结果生成提升中标率的建议"""
    recommendations = []

    dim_scores = factors.get("dimension_scores", {})

    # 1. 五维评估低分项建议
    if dim_scores.get("requirement_maturity", 100) < 60:
        recommendations.append("需求成熟度较低，建议与客户进一步澄清需求")
    if dim_scores.get("technical_feasibility", 100) < 60:
        recommendations.append("技术可行性评分较低，建议投入更多技术资源评估方案")
    if dim_scores.get("business_feasibility", 100) < 60:
        recommendations.append("商务可行性评分较低，建议重新评估定价策略")
    if dim_scores.get("delivery_risk", 100) < 60:
        recommendations.append("交付风险评分高，建议制定详细的风险应对计划")
    if dim_scores.get("customer_relationship", 100) < 60:
        recommendations.append("客户关系评分较低，建议加强客户高层关系维护")

    # 2. 销售人员建议
    if factors.get("salesperson_win_rate", 1) < 0.3:
        recommendations.append("销售人员历史中标率较低，建议派遣经验丰富的销售支援")

    # 3. 竞争态势建议
    if factors.get("competitor_count", 0) > 3:
        recommendations.append("竞争对手较多，建议突出差异化优势")

    # 4. 整体建议
    if predicted_rate < 0.4:
        recommendations.append("预测中标率偏低，建议评估是否继续投入资源")
    elif predicted_rate >= 0.7:
        recommendations.append("中标概率较高，建议重点关注，确保资源到位")

    return recommendations


@router.post("/predict-win-rate", response_model=ResponseModel[WinRatePredictionResponse])
async def predict_win_rate(
    request: WinRatePredictionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """预测线索中标概率"""

    # 获取销售人员历史中标率
    salesperson_stats = db.query(
        func.count(Project.id).label('total'),
        func.sum(func.case((Project.outcome == LeadOutcomeEnum.WON.value, 1), else_=0)).label('won')
    ).filter(
        Project.salesperson_id == request.salesperson_id,
        Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
    ).first()

    total = salesperson_stats.total or 0
    won = salesperson_stats.won or 0
    salesperson_win_rate = won / total if total > 0 else 0.2  # 默认20%

    # 获取客户历史合作次数
    customer_cooperation_count = 0
    if request.customer_id:
        customer_cooperation_count = db.query(func.count(Project.id)).filter(
            Project.customer_id == request.customer_id,
            Project.outcome == LeadOutcomeEnum.WON.value
        ).scalar() or 0

    # 计算预测中标率
    predicted_rate, level, factors = calculate_win_rate(
        dimension_scores=request.dimension_scores,
        salesperson_win_rate=salesperson_win_rate,
        customer_cooperation_count=customer_cooperation_count,
        competitor_count=request.competitor_count or 3,
        is_repeat_customer=request.is_repeat_customer
    )

    # 获取建议
    recommendations = get_win_rate_recommendations(predicted_rate, factors)

    # 查找相似线索
    similar_count = db.query(func.count(Project.id)).filter(
        Project.evaluation_score.between(
            request.dimension_scores.total_score - 10,
            request.dimension_scores.total_score + 10
        ),
        Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
    ).scalar() or 0

    similar_won = db.query(func.count(Project.id)).filter(
        Project.evaluation_score.between(
            request.dimension_scores.total_score - 10,
            request.dimension_scores.total_score + 10
        ),
        Project.outcome == LeadOutcomeEnum.WON.value
    ).scalar() or 0

    similar_win_rate = similar_won / similar_count if similar_count > 0 else None

    return ResponseModel(
        code=200,
        message="预测成功",
        data=WinRatePredictionResponse(
            predicted_win_rate=round(predicted_rate, 3),
            probability_level=level,
            confidence=0.7 if total > 10 else 0.5,  # 样本越多置信度越高
            factors=factors,
            recommendations=recommendations,
            similar_leads_count=similar_count,
            similar_leads_win_rate=round(similar_win_rate, 3) if similar_win_rate else None
        )
    )


# ==================== 资源投入分析 ====================

@router.get("/lead/{lead_id}/resource-investment", response_model=ResponseModel[ResourceInvestmentSummary])
async def get_lead_resource_investment(
    lead_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """获取某线索/项目投入的资源工时"""

    # 尝试通过线索号或项目号查找
    project_code = convert_lead_code_to_project_code(lead_id) if lead_id.startswith('XS') else lead_id

    project = db.query(Project).filter(
        or_(
            Project.project_code == project_code,
            Project.source_lead_id == lead_id
        )
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail=f"未找到线索/项目: {lead_id}")

    # 查询工时记录（从 Timesheet 或 WorkLog 表）
    # 这里假设使用 work_log 表
    from app.models.work_log import WorkLog

    work_logs = db.query(WorkLog).filter(WorkLog.project_id == project.id).all()

    total_hours = sum(log.work_hours or 0 for log in work_logs)
    engineer_ids = set(log.employee_id for log in work_logs if log.employee_id)

    # 按员工汇总
    engineer_hours = {}
    for log in work_logs:
        emp_id = log.employee_id
        if emp_id not in engineer_hours:
            engineer_hours[emp_id] = 0
        engineer_hours[emp_id] += log.work_hours or 0

    engineers = [
        {"employee_id": emp_id, "hours": hours}
        for emp_id, hours in engineer_hours.items()
    ]

    # 按月份汇总
    investment_by_month = {}
    for log in work_logs:
        month_key = log.work_date.strftime('%Y-%m') if log.work_date else 'unknown'
        if month_key not in investment_by_month:
            investment_by_month[month_key] = 0
        investment_by_month[month_key] += log.work_hours or 0

    hourly_rate = Decimal('300')  # 可配置
    estimated_cost = Decimal(str(total_hours)) * hourly_rate

    return ResponseModel(
        code=200,
        message="查询成功",
        data=ResourceInvestmentSummary(
            lead_id=lead_id,
            lead_name=project.name,
            total_hours=total_hours,
            engineer_hours=total_hours,  # 简化处理
            presales_hours=0,
            design_hours=0,
            engineer_count=len(engineer_ids),
            engineers=engineers,
            estimated_cost=estimated_cost,
            hourly_rate=hourly_rate,
            investment_by_stage={},
            investment_by_month=investment_by_month
        )
    )


# ==================== 资源浪费分析 ====================

@router.get("/resource-waste-analysis", response_model=ResponseModel[ResourceWasteAnalysis])
async def get_resource_waste_analysis(
    period: str = Query(..., description="分析周期，格式 YYYY-MM 或 YYYY"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """获取资源浪费分析报告"""

    # 解析周期
    if len(period) == 7:  # YYYY-MM
        year = int(period[:4])
        month = int(period[5:7])
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
    else:  # YYYY
        year = int(period)
        start_date = date(year, 1, 1)
        end_date = date(year + 1, 1, 1)

    # 查询该周期内的项目
    projects = db.query(Project).filter(
        Project.created_at >= start_date,
        Project.created_at < end_date,
        Project.outcome.isnot(None)
    ).all()

    total_leads = len(projects)
    won_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.WON.value)
    lost_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.LOST.value)
    abandoned_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.ABANDONED.value)
    pending_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.PENDING.value)

    overall_win_rate = won_leads / (won_leads + lost_leads) if (won_leads + lost_leads) > 0 else 0

    # 计算资源投入
    from app.models.work_log import WorkLog

    total_investment_hours = 0
    wasted_hours = 0
    loss_reasons = {}

    for project in projects:
        project_hours = db.query(func.sum(WorkLog.work_hours)).filter(
            WorkLog.project_id == project.id
        ).scalar() or 0

        total_investment_hours += project_hours

        if project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
            wasted_hours += project_hours
            reason = project.loss_reason or 'OTHER'
            loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    hourly_rate = Decimal('300')
    wasted_cost = Decimal(str(wasted_hours)) * hourly_rate
    waste_rate = wasted_hours / total_investment_hours if total_investment_hours > 0 else 0

    return ResponseModel(
        code=200,
        message="分析成功",
        data=ResourceWasteAnalysis(
            analysis_period=period,
            total_leads=total_leads,
            won_leads=won_leads,
            lost_leads=lost_leads,
            abandoned_leads=abandoned_leads,
            pending_leads=pending_leads,
            overall_win_rate=round(overall_win_rate, 3),
            total_investment_hours=total_investment_hours,
            wasted_hours=wasted_hours,
            wasted_cost=wasted_cost,
            waste_rate=round(waste_rate, 3),
            loss_reasons=loss_reasons
        )
    )


# ==================== 销售人员绩效分析 ====================

@router.get("/salesperson/{salesperson_id}/performance", response_model=ResponseModel[SalespersonPerformance])
async def get_salesperson_performance(
    salesperson_id: int,
    period: Optional[str] = Query(None, description="统计周期，格式 YYYY 或 YYYY-MM，默认全部"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """获取销售人员绩效分析"""

    # 获取销售人员信息
    salesperson = db.query(User).filter(User.id == salesperson_id).first()
    if not salesperson:
        raise HTTPException(status_code=404, detail="销售人员不存在")

    # 构建查询条件
    query = db.query(Project).filter(Project.salesperson_id == salesperson_id)

    if period:
        if len(period) == 7:  # YYYY-MM
            year, month = int(period[:4]), int(period[5:7])
            start_date = date(year, month, 1)
            end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        else:  # YYYY
            year = int(period)
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)
        query = query.filter(Project.created_at >= start_date, Project.created_at < end_date)

    projects = query.all()

    total_leads = len(projects)
    won_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.WON.value)
    lost_leads = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.LOST.value)
    win_rate = won_leads / (won_leads + lost_leads) if (won_leads + lost_leads) > 0 else 0

    total_estimated_amount = sum(p.contract_amount or Decimal('0') for p in projects)
    won_amount = sum(p.contract_amount or Decimal('0') for p in projects if p.outcome == LeadOutcomeEnum.WON.value)

    # 计算资源消耗
    from app.models.work_log import WorkLog

    total_resource_hours = 0
    wasted_hours = 0
    loss_reason_count = {}

    for project in projects:
        hours = db.query(func.sum(WorkLog.work_hours)).filter(
            WorkLog.project_id == project.id
        ).scalar() or 0
        total_resource_hours += hours

        if project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
            wasted_hours += hours
            reason = project.loss_reason or 'OTHER'
            loss_reason_count[reason] = loss_reason_count.get(reason, 0) + 1

    # 资源效率（中标金额/消耗工时）
    resource_efficiency = float(won_amount) / total_resource_hours if total_resource_hours > 0 else 0

    # 主要丢标原因（Top 3）
    top_loss_reasons = sorted(loss_reason_count.items(), key=lambda x: x[1], reverse=True)[:3]
    top_loss_reasons = [{"reason": r, "count": c} for r, c in top_loss_reasons]

    # 月度趋势（近6个月）
    monthly_trend = []
    today = date.today()
    for i in range(5, -1, -1):
        month_date = date(today.year, today.month, 1) - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')

        month_projects = [p for p in projects if p.created_at and p.created_at.strftime('%Y-%m') == month_key]
        month_won = sum(1 for p in month_projects if p.outcome == LeadOutcomeEnum.WON.value)
        month_lost = sum(1 for p in month_projects if p.outcome == LeadOutcomeEnum.LOST.value)
        month_rate = month_won / (month_won + month_lost) if (month_won + month_lost) > 0 else 0

        monthly_trend.append({
            "month": month_key,
            "total": len(month_projects),
            "won": month_won,
            "lost": month_lost,
            "win_rate": round(month_rate, 3)
        })

    return ResponseModel(
        code=200,
        message="查询成功",
        data=SalespersonPerformance(
            salesperson_id=salesperson_id,
            salesperson_name=salesperson.name or salesperson.username,
            department=salesperson.department_id,
            total_leads=total_leads,
            won_leads=won_leads,
            lost_leads=lost_leads,
            win_rate=round(win_rate, 3),
            total_estimated_amount=total_estimated_amount,
            won_amount=won_amount,
            total_resource_hours=total_resource_hours,
            wasted_hours=wasted_hours,
            resource_efficiency=round(resource_efficiency, 2),
            top_loss_reasons=top_loss_reasons,
            monthly_trend=monthly_trend
        )
    )


@router.get("/salesperson-ranking", response_model=ResponseModel[SalespersonRanking])
async def get_salesperson_ranking(
    ranking_type: str = Query("win_rate", description="排行类型: win_rate/efficiency/amount"),
    period: str = Query(..., description="统计周期，格式 YYYY 或 YYYY-MM"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """获取销售人员排行榜"""

    # 获取所有销售人员
    salespeople = db.query(User).filter(User.role == 'sales').all()

    performances = []
    for sp in salespeople:
        # 简化处理：直接构建统计数据
        query = db.query(Project).filter(Project.salesperson_id == sp.id)

        if len(period) == 7:
            year, month = int(period[:4]), int(period[5:7])
            start_date = date(year, month, 1)
            end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        else:
            year = int(period)
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)

        query = query.filter(Project.created_at >= start_date, Project.created_at < end_date)
        projects = query.all()

        if not projects:
            continue

        total = len(projects)
        won = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.WON.value)
        lost = sum(1 for p in projects if p.outcome == LeadOutcomeEnum.LOST.value)
        win_rate = won / (won + lost) if (won + lost) > 0 else 0
        won_amount = sum(p.contract_amount or Decimal('0') for p in projects if p.outcome == LeadOutcomeEnum.WON.value)

        performances.append(SalespersonPerformance(
            salesperson_id=sp.id,
            salesperson_name=sp.name or sp.username,
            total_leads=total,
            won_leads=won,
            lost_leads=lost,
            win_rate=round(win_rate, 3),
            won_amount=won_amount,
            total_estimated_amount=Decimal('0'),
            total_resource_hours=0,
            wasted_hours=0,
            resource_efficiency=0
        ))

    # 排序
    if ranking_type == "win_rate":
        performances.sort(key=lambda x: x.win_rate, reverse=True)
    elif ranking_type == "efficiency":
        performances.sort(key=lambda x: x.resource_efficiency, reverse=True)
    elif ranking_type == "amount":
        performances.sort(key=lambda x: x.won_amount, reverse=True)

    return ResponseModel(
        code=200,
        message="查询成功",
        data=SalespersonRanking(
            ranking_type=ranking_type,
            period=period,
            rankings=performances[:limit]
        )
    )


# ==================== 仪表板 ====================

@router.get("/dashboard", response_model=ResponseModel[PresalesDashboardData])
async def get_presales_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """获取售前分析仪表板数据"""

    today = date.today()
    year_start = date(today.year, 1, 1)

    # 年度统计
    ytd_projects = db.query(Project).filter(
        Project.created_at >= year_start
    ).all()

    total_leads_ytd = len(ytd_projects)
    won_leads_ytd = sum(1 for p in ytd_projects if p.outcome == LeadOutcomeEnum.WON.value)
    lost_leads_ytd = sum(1 for p in ytd_projects if p.outcome == LeadOutcomeEnum.LOST.value)
    overall_win_rate = won_leads_ytd / (won_leads_ytd + lost_leads_ytd) if (won_leads_ytd + lost_leads_ytd) > 0 else 0

    # 资源浪费统计
    from app.models.work_log import WorkLog

    total_hours = 0
    wasted_hours = 0
    loss_reasons = {}

    for project in ytd_projects:
        hours = db.query(func.sum(WorkLog.work_hours)).filter(
            WorkLog.project_id == project.id
        ).scalar() or 0
        total_hours += hours

        if project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
            wasted_hours += hours
            reason = project.loss_reason or 'OTHER'
            loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    avg_investment = total_hours / total_leads_ytd if total_leads_ytd > 0 else 0
    waste_rate = wasted_hours / total_hours if total_hours > 0 else 0
    wasted_cost = Decimal(str(wasted_hours)) * Decimal('300')

    # 月度统计（近6个月）
    monthly_stats = []
    for i in range(5, -1, -1):
        month_date = date(today.year, today.month, 1) - timedelta(days=30 * i)
        month_key = month_date.strftime('%Y-%m')

        month_projects = [p for p in ytd_projects if p.created_at and p.created_at.strftime('%Y-%m') == month_key]
        month_won = sum(1 for p in month_projects if p.outcome == LeadOutcomeEnum.WON.value)
        month_lost = sum(1 for p in month_projects if p.outcome == LeadOutcomeEnum.LOST.value)

        monthly_stats.append({
            "month": month_key,
            "total": len(month_projects),
            "won": month_won,
            "lost": month_lost,
            "win_rate": round(month_won / (month_won + month_lost), 3) if (month_won + month_lost) > 0 else 0
        })

    return ResponseModel(
        code=200,
        message="查询成功",
        data=PresalesDashboardData(
            total_leads_ytd=total_leads_ytd,
            won_leads_ytd=won_leads_ytd,
            overall_win_rate=round(overall_win_rate, 3),
            avg_investment_per_lead=round(avg_investment, 1),
            total_wasted_hours=wasted_hours,
            total_wasted_cost=wasted_cost,
            waste_rate=round(waste_rate, 3),
            monthly_stats=monthly_stats,
            loss_reason_distribution=loss_reasons
        )
    )
