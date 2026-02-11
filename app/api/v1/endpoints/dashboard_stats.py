# -*- coding: utf-8 -*-
"""
统一工作台统计 API

根据用户角色返回相应的统计数据：
- sales: 销售相关（线索、商机、合同、收入）
- engineer: 工程相关（任务、工时、ECN、评审）
- procurement: 采购相关（订单、待确认、逾期、节省）
- production: 生产相关（工单、进行中、完成、良品率）
- pmo: PMO相关（活跃项目、进度、延期、完成）
- admin: 管理员相关（用户、角色、登录、错误）
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range, get_last_month_range, get_week_range
from app.common.query_filters import apply_keyword_filter
from app.common.statistics import (
    calculate_trend,
    create_stat_card,
    create_stats_response,
    format_currency,
    format_hours,
    format_percentage,
)
from app.core import security
from app.models.user import User, Role
from app.models.project import Project
from app.models.purchase import PurchaseOrder
from app.models.sales.leads import Lead, Opportunity
from app.models.sales.contracts import Contract
from app.models.timesheet import Timesheet
from app.models.ecn.core import Ecn
from app.models.ecn.evaluation_approval import EcnEvaluation, EcnApproval
from app.models.task_center import TaskUnified
from app.models.production.work_order import WorkOrder
from app.schemas.common import ResponseModel

router = APIRouter()


# TODO: [租户隔离] 当前业务模型(Lead/Contract/PurchaseOrder/WorkOrder等)缺少tenant_id字段
# 租户隔离主要通过User的数据权限范围（DataScopeService）实现
# 建议在后续重构中为所有业务模型添加tenant_id字段以支持真正的多租户隔离
# 参考: get_pmo_stats() 使用 DataScopeService.filter_projects_by_scope() 进行权限过滤


def get_sales_stats(db: Session, current_user: User) -> dict:
    """获取销售统计数据

    统计内容：
    - 活跃线索：状态不是 CONVERTED/LOST 的线索数
    - 商机数：阶段不是 WON/LOST 的商机数
    - 合同数：状态为 SIGNED/ACTIVE 的合同数
    - 本月签约：本月签订的合同总金额
    """
    today = date.today()
    month_start, month_end = get_month_range(today)
    last_month_start, last_month_end = get_last_month_range(today)

    # 活跃线索统计
    active_leads = db.query(func.count(Lead.id)).filter(
        Lead.status.notin_(['CONVERTED', 'LOST'])
    ).scalar() or 0

    last_month_leads = db.query(func.count(Lead.id)).filter(
        Lead.status.notin_(['CONVERTED', 'LOST']),
        Lead.created_at < month_start
    ).scalar() or 0

    leads_trend = calculate_trend(active_leads, last_month_leads)

    # 商机统计
    active_opportunities = db.query(func.count(Opportunity.id)).filter(
        Opportunity.stage.notin_(['WON', 'LOST'])
    ).scalar() or 0

    # 合同统计（已签约/执行中）
    active_contracts = db.query(func.count(Contract.id)).filter(
        Contract.status.in_(['SIGNED', 'ACTIVE'])
    ).scalar() or 0

    # 本月签约金额
    monthly_revenue = db.query(func.sum(Contract.contract_amount)).filter(
        Contract.signed_date >= month_start,
        Contract.signed_date <= month_end,
        Contract.status.in_(['SIGNED', 'ACTIVE', 'COMPLETED'])
    ).scalar() or Decimal('0')

    # 上月签约金额（用于计算趋势）
    last_month_revenue = db.query(func.sum(Contract.contract_amount)).filter(
        Contract.signed_date >= last_month_start,
        Contract.signed_date <= last_month_end,
        Contract.status.in_(['SIGNED', 'ACTIVE', 'COMPLETED'])
    ).scalar() or Decimal('0')

    revenue_trend = calculate_trend(monthly_revenue, last_month_revenue)

    return create_stats_response([
        create_stat_card('leads', '活跃线索', active_leads, trend=leads_trend),
        create_stat_card('opportunities', '商机数', active_opportunities),
        create_stat_card('contracts', '合同数', active_contracts),
        create_stat_card('revenue', '本月签约', format_currency(monthly_revenue), trend=revenue_trend),
    ])


def get_engineer_stats(db: Session, current_user: User) -> dict:
    """获取工程师统计数据

    统计内容：
    - 待办任务：当前用户未完成的任务数
    - 本周工时：当前用户本周已记录的工时
    - 待处理ECN：当前用户需要处理的ECN数量
    - 待评审：当前用户待评审的ECN评估/审批数
    """
    today = date.today()
    week_start, week_end = get_week_range(today)
    last_week_start, last_week_end = get_week_range(today - timedelta(days=7))

    user_id = current_user.id

    # 待办任务统计（未完成的任务）
    pending_tasks = db.query(func.count(TaskUnified.id)).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.is_active == True,
        TaskUnified.status.in_(['PENDING', 'ACCEPTED', 'IN_PROGRESS', 'PAUSED'])
    ).scalar() or 0

    # 本周工时统计
    weekly_hours = db.query(func.sum(Timesheet.hours)).filter(
        Timesheet.user_id == user_id,
        Timesheet.work_date >= week_start,
        Timesheet.work_date <= week_end,
        Timesheet.status.in_(['SUBMITTED', 'APPROVED'])
    ).scalar() or Decimal('0')

    # 上周工时（用于趋势计算）
    last_week_hours = db.query(func.sum(Timesheet.hours)).filter(
        Timesheet.user_id == user_id,
        Timesheet.work_date >= last_week_start,
        Timesheet.work_date <= last_week_end,
        Timesheet.status.in_(['SUBMITTED', 'APPROVED'])
    ).scalar() or Decimal('0')

    hours_trend = calculate_trend(weekly_hours, last_week_hours)

    # 待处理ECN（用户提交的待审核ECN）
    pending_ecn = db.query(func.count(Ecn.id)).filter(
        Ecn.applicant_id == user_id,
        Ecn.status.in_(['DRAFT', 'PENDING_REVIEW'])
    ).scalar() or 0

    # 待评审数量（需要当前用户评审/审批的ECN）
    pending_evaluations = db.query(func.count(EcnEvaluation.id)).filter(
        EcnEvaluation.evaluator_id == user_id,
        EcnEvaluation.status == 'PENDING'
    ).scalar() or 0

    pending_approvals = db.query(func.count(EcnApproval.id)).filter(
        EcnApproval.approver_id == user_id,
        EcnApproval.status == 'PENDING'
    ).scalar() or 0

    pending_reviews = pending_evaluations + pending_approvals

    return create_stats_response([
        create_stat_card('tasks', '待办任务', pending_tasks),
        create_stat_card('hours-logged', '本周工时', format_hours(weekly_hours), trend=round(hours_trend, 1)),
        create_stat_card('ecn-pending', '待处理ECN', pending_ecn),
        create_stat_card('reviews', '待评审', pending_reviews),
    ])


def get_procurement_stats(db: Session, current_user: User) -> dict:
    """获取采购统计数据"""
    # 定义活跃状态（排除草稿和已取消）
    active_statuses = ['SUBMITTED', 'APPROVED', 'CONFIRMED', 'PARTIAL_RECEIVED']
    pending_statuses = ['SUBMITTED', 'APPROVED']  # 待确认状态
    not_completed_statuses = ['SUBMITTED', 'APPROVED', 'CONFIRMED', 'PARTIAL_RECEIVED']

    # 统计活跃采购订单数量
    total_orders = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status.in_(active_statuses)
    ).scalar() or 0

    # 统计待确认订单数量（已提交/已审批但供应商未确认）
    pending_orders = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status.in_(pending_statuses)
    ).scalar() or 0

    # 统计逾期订单数量（要求交期已过但未完成收货）
    today = date.today()
    overdue_orders = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status.in_(not_completed_statuses),
        PurchaseOrder.required_date < today
    ).scalar() or 0

    # 节省金额暂无比较数据，保持为0
    savings = 0

    return create_stats_response([
        create_stat_card('orders', '采购订单', total_orders),
        create_stat_card('pending', '待确认', pending_orders),
        create_stat_card('overdue', '逾期', overdue_orders),
        create_stat_card('savings', '节省金额', format_currency(savings)),
    ])


def get_production_stats(db: Session, current_user: User) -> dict:
    """获取生产统计数据

    统计内容：
    - 工单数：活跃工单总数（排除已取消）
    - 进行中：正在执行的工单数
    - 已完成：本月完成的工单数
    - 良品率：合格数量/完成数量的百分比
    """
    today = date.today()
    month_start, month_end = get_month_range(today)

    # 活跃工单（排除已取消）
    active_statuses = ['PENDING', 'ASSIGNED', 'STARTED', 'PAUSED', 'COMPLETED', 'APPROVED']
    total_orders = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(active_statuses)
    ).scalar() or 0

    # 进行中工单
    in_progress = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(['STARTED', 'PAUSED'])
    ).scalar() or 0

    # 本月已完成工单
    completed = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(['COMPLETED', 'APPROVED']),
        WorkOrder.actual_end_time >= month_start,
        WorkOrder.actual_end_time <= datetime.combine(month_end, datetime.max.time())
    ).scalar() or 0

    # 良品率计算（合格数量 / 完成数量）
    yield_data = db.query(
        func.sum(WorkOrder.qualified_qty),
        func.sum(WorkOrder.completed_qty)
    ).filter(
        WorkOrder.status.in_(['COMPLETED', 'APPROVED']),
        WorkOrder.completed_qty > 0
    ).first()

    total_qualified = yield_data[0] or 0
    total_completed_qty = yield_data[1] or 0

    if total_completed_qty > 0:
        yield_rate = (total_qualified / total_completed_qty) * 100
        yield_str = format_percentage(yield_rate)
    else:
        yield_str = '-'

    return create_stats_response([
        create_stat_card('work-orders', '工单数', total_orders),
        create_stat_card('in-progress', '进行中', in_progress),
        create_stat_card('completed', '已完成', completed),
        create_stat_card('yield', '良品率', yield_str),
    ])


def get_pmo_stats(db: Session, current_user: User) -> dict:
    """获取PMO统计数据"""
    # 应用数据权限过滤
    from app.services.data_scope import DataScopeService
    query = db.query(Project).filter(Project.is_active == True)
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    projects = query.all()

    # 统计项目数据
    total = len(projects)

    # 按健康度统计
    on_track = sum(1 for p in projects if p.health == 'H1')
    delayed = sum(1 for p in projects if p.health in ['H2', 'H3'])
    completed = sum(1 for p in projects if p.health == 'H4')

    return create_stats_response([
        create_stat_card('active-projects', '活跃项目', total),
        create_stat_card('on-track', '正常进度', on_track),
        create_stat_card('delayed', '延期项目', delayed),
        create_stat_card('completed', '已完成', completed),
    ])


def get_admin_stats(db: Session, current_user: User) -> dict:
    """获取管理员统计数据"""
    from app.models.permission import PermissionAudit

    today = date.today()

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_roles = db.query(func.count(Role.id)).scalar() or 0

    # 今日审计操作次数（使用权限审计表统计今日活动）
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    login_count_today = db.query(func.count(PermissionAudit.id)).filter(
        PermissionAudit.action == 'login',
        PermissionAudit.created_at >= today_start,
        PermissionAudit.created_at <= today_end
    ).scalar() or 0

    # 如果没有登录审计，使用今日总审计操作数作为活跃度指标
    if login_count_today == 0:
        login_count_today = db.query(func.count(PermissionAudit.id)).filter(
            PermissionAudit.created_at >= today_start,
            PermissionAudit.created_at <= today_end
        ).scalar() or 0

    # TODO: 需要添加系统错误日志表来统计错误数
    # 当前从审计表中查询今日失败操作作为替代
    error_query = db.query(func.count(PermissionAudit.id)).filter(
        PermissionAudit.created_at >= today_start,
        PermissionAudit.created_at <= today_end
    )
    error_query = apply_keyword_filter(
        error_query,
        PermissionAudit,
        "fail",
        "action",
        use_ilike=False,
    )
    error_count = error_query.scalar() or 0

    return create_stats_response([
        create_stat_card('users', '用户数', total_users),
        create_stat_card('roles', '角色数', total_roles),
        create_stat_card('logins', '今日活跃', login_count_today),
        create_stat_card('errors', '系统错误', error_count),
    ])


# 类型映射到统计函数
STATS_FUNCTIONS = {
    'sales': get_sales_stats,
    'engineer': get_engineer_stats,
    'procurement': get_procurement_stats,
    'production': get_production_stats,
    'pmo': get_pmo_stats,
    'admin': get_admin_stats,
}


@router.get("/dashboard/stats/{stats_type}", response_model=ResponseModel)
def get_dashboard_stats(
    stats_type: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取统一工作台统计数据

    根据stats_type返回不同类型的统计数据：
    - sales: 销售统计（线索、商机、合同、收入）
    - engineer: 工程统计（任务、工时、ECN、评审）
    - procurement: 采购统计（订单、待确认、逾期、节省）
    - production: 生产统计（工单、进行中、完成、良品率）
    - pmo: PMO统计（项目、进度、延期、完成）
    - admin: 管理员统计（用户、角色、登录、错误）
    """
    # 验证stats_type是否有效
    if stats_type not in STATS_FUNCTIONS:
        return ResponseModel(
            code=400,
            message=f"不支持的统计类型: {stats_type}",
            data=None
        )

    # 获取对应的统计函数
    stats_func = STATS_FUNCTIONS[stats_type]

    # 调用统计函数获取数据
    try:
        stats_data = stats_func(db, current_user)
        return ResponseModel(
            code=200,
            message="success",
            data=stats_data
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"获取统计数据失败: {str(e)}",
            data=None
        )
