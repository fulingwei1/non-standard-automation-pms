# -*- coding: utf-8 -*-
"""
售前工单管理 - CRUD操作
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import can_manage_sales_opportunity
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.presale import PresaleSupportTicket
from app.models.sales import Opportunity
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.presale import TicketCreate, TicketResponse

from .utils import build_ticket_response, generate_ticket_no
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def read_tickets(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（工单编号/标题）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    ticket_type: Optional[str] = Query(None, description="工单类型筛选"),
    applicant_id: Optional[int] = Query(None, description="申请人ID筛选"),
    assignee_id: Optional[int] = Query(None, description="处理人ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单列表
    """
    query = db.query(PresaleSupportTicket)

    query = apply_keyword_filter(query, PresaleSupportTicket, keyword, ["ticket_no", "title"])

    if status:
        if "," in status:
            status_values = [item.strip() for item in status.split(",") if item.strip()]
            if status_values:
                query = query.filter(PresaleSupportTicket.status.in_(status_values))
        else:
            query = query.filter(PresaleSupportTicket.status == status)

    if ticket_type:
        query = query.filter(PresaleSupportTicket.ticket_type == ticket_type)

    if applicant_id:
        query = query.filter(PresaleSupportTicket.applicant_id == applicant_id)

    if assignee_id:
        query = query.filter(PresaleSupportTicket.assignee_id == assignee_id)

    if customer_id:
        query = query.filter(PresaleSupportTicket.customer_id == customer_id)

    total = query.count()
    tickets = apply_pagination(query.order_by(desc(PresaleSupportTicket.created_at)), pagination.offset, pagination.limit).all()

    items = [build_ticket_response(ticket) for ticket in tickets]

    return pagination.to_response(items, total)


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: TicketCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建支持申请（已集成PM介入策略判断）
    """
    from datetime import datetime
    from app.services.pm_involvement_service import PMInvolvementService
    import logging
    
    logger = logging.getLogger(__name__)

    if ticket_in.ticket_type == 'SOLUTION_REVIEW':
        if not ticket_in.opportunity_id:
            raise HTTPException(status_code=400, detail="方案评审必须关联商机")
        opportunity = get_or_404(db, Opportunity, ticket_in.opportunity_id, "商机不存在")
        gate_status = (opportunity.gate_status or "").upper()
        if gate_status not in {"PASS", "PASSED"}:
            raise HTTPException(status_code=400, detail="商机阶段门未通过，无法申请评审")
        if not can_manage_sales_opportunity(db, current_user, opportunity):
            raise HTTPException(status_code=403, detail="无权限为该商机申请评审")

    ticket_status = 'REVIEW' if ticket_in.ticket_type == 'SOLUTION_REVIEW' else 'PENDING'
    
    # 创建工单基本信息
    ticket = PresaleSupportTicket(
        ticket_no=generate_ticket_no(db),
        title=ticket_in.title,
        ticket_type=ticket_in.ticket_type,
        urgency=ticket_in.urgency,
        description=ticket_in.description,
        customer_id=ticket_in.customer_id,
        customer_name=ticket_in.customer_name,
        opportunity_id=ticket_in.opportunity_id,
        project_id=ticket_in.project_id,
        applicant_id=current_user.id,
        applicant_name=current_user.real_name or current_user.username,
        applicant_dept=current_user.department,
        apply_time=datetime.now(),
        expected_date=ticket_in.expected_date,
        deadline=ticket_in.deadline,
        status=ticket_status,
        created_by=current_user.id
    )
    
    # ========================================
    # PM介入策略判断（2026-02-15新增）
    # ========================================
    try:
        # 准备项目数据（从工单信息中提取）
        project_data = {
            "项目金额": getattr(ticket_in, 'estimated_amount', 0),
            "项目类型": ticket_in.title or "",  # 从标题推断项目类型
            "行业": getattr(ticket_in, 'industry', ""),
            "是否首次做": getattr(ticket_in, 'is_first_time', False),
            "历史相似项目数": 0,  # 需要从数据库查询（暂时默认0）
            "失败项目数": 0,  # 需要从数据库查询（暂时默认0）
            "是否有标准方案": getattr(ticket_in, 'has_standard_solution', False),
            "技术创新点": getattr(ticket_in, 'innovation_points', [])
        }
        
        # 调用PM介入判断服务
        pm_result = PMInvolvementService.judge_pm_involvement_timing(project_data)
        
        # 保存判断结果到工单
        ticket.pm_involvement_required = pm_result.get('需要PM审核', False)
        ticket.pm_involvement_risk_level = pm_result.get('风险等级', '低')
        ticket.pm_involvement_risk_factors = pm_result.get('原因', [])
        ticket.pm_involvement_checked_at = datetime.now()
        
        # 如果需要PM提前介入，记录日志并发送通知
        if ticket.pm_involvement_required:
            logger.warning(
                f"工单 {ticket.ticket_no} 需要PM提前介入！"
                f"风险等级: {ticket.pm_involvement_risk_level}, "
                f"风险因素数: {pm_result.get('风险因素数', 0)}"
            )
            
            # 发送通知给PMO（企业微信/钉钉）
            try:
                PMInvolvementService.generate_notification_message(
                    pm_result,
                    {
                        "项目名称": ticket.title,
                        "客户名称": ticket.customer_name or "未知",
                        "预估金额": project_data.get("项目金额", 0)
                    }
                )
                # TODO: 调用企业微信/钉钉通知接口
                # send_wechat_notification(notification_message)
                logger.info(f"PM介入通知已生成（待集成通知渠道）")
            except Exception as e:
                logger.error(f"发送PM介入通知失败: {e}")
    
    except Exception as e:
        # PM介入判断失败不影响工单创建
        logger.error(f"PM介入策略判断失败: {e}", exc_info=True)
        ticket.pm_involvement_required = False
        ticket.pm_involvement_risk_level = '低'
    
    # 保存工单
    save_obj(db, ticket)

    return build_ticket_response(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
def read_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单详情
    """
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    return build_ticket_response(ticket)
