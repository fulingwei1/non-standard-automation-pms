# -*- coding: utf-8 -*-
"""
回款催收 API endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.business_support import PaymentReminder
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import (
    PaymentReminderCreate,
    PaymentReminderResponse,
    PaymentReminderUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _payment_reminder_response(reminder: PaymentReminder) -> PaymentReminderResponse:
    return PaymentReminderResponse(
        id=reminder.id,
        contract_id=reminder.contract_id,
        project_id=reminder.project_id,
        payment_node=reminder.payment_node,
        payment_amount=reminder.payment_amount,
        plan_date=reminder.plan_date,
        reminder_type=reminder.reminder_type,
        reminder_content=reminder.reminder_content,
        reminder_date=reminder.reminder_date,
        reminder_person_id=reminder.reminder_person_id,
        customer_response=reminder.customer_response,
        next_reminder_date=reminder.next_reminder_date,
        status=reminder.status,
        remark=reminder.remark,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )


@router.post("", response_model=ResponseModel[PaymentReminderResponse], summary="创建回款催收记录")
async def create_payment_reminder(
    reminder_data: PaymentReminderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create")),
):
    """创建回款催收记录"""
    try:
        # 检查合同是否存在
        if reminder_data.contract_id:
            get_or_404(db, Contract, reminder_data.contract_id, "合同不存在")

        # 创建催收记录
        reminder = PaymentReminder(
            contract_id=reminder_data.contract_id,
            project_id=reminder_data.project_id,
            payment_node=reminder_data.payment_node,
            payment_amount=reminder_data.payment_amount,
            plan_date=reminder_data.plan_date,
            reminder_type=reminder_data.reminder_type,
            reminder_content=reminder_data.reminder_content,
            reminder_date=reminder_data.reminder_date,
            reminder_person_id=current_user.id,
            customer_response=reminder_data.customer_response,
            next_reminder_date=reminder_data.next_reminder_date,
            status="pending",
            remark=reminder_data.remark,
        )

        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        return ResponseModel(
            code=200,
            message="创建回款催收记录成功",
            data=_payment_reminder_response(reminder),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建回款催收记录失败: {str(e)}")


@router.get(
    "",
    response_model=ResponseModel[PaginatedResponse[PaymentReminderResponse]],
    summary="获取回款催收记录列表",
)
async def get_payment_reminders(
    pagination: PaginationParams = Depends(get_pagination_query),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    reminder_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read")),
):
    """获取回款催收记录列表"""
    try:
        query = db.query(PaymentReminder)

        # 筛选条件
        if contract_id:
            query = query.filter(PaymentReminder.contract_id == contract_id)
        if project_id:
            query = query.filter(PaymentReminder.project_id == project_id)
        if reminder_status:
            query = query.filter(PaymentReminder.status == reminder_status)

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(PaymentReminder.reminder_date))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        # 转换为响应格式
        reminder_list = [_payment_reminder_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取回款催收记录列表成功",
            data=PaginatedResponse(
                items=reminder_list,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回款催收记录列表失败: {str(e)}")


@router.get(
    "/{reminder_id}",
    response_model=ResponseModel[PaymentReminderResponse],
    summary="获取回款催收记录详情",
)
async def get_payment_reminder(
    reminder_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read")),
):
    """获取回款催收记录详情。"""
    try:
        reminder = get_or_404(db, PaymentReminder, reminder_id, "回款催收记录不存在")
        return ResponseModel(
            code=200,
            message="获取回款催收记录详情成功",
            data=_payment_reminder_response(reminder),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回款催收记录详情失败: {str(e)}")


@router.put(
    "/{reminder_id}",
    response_model=ResponseModel[PaymentReminderResponse],
    summary="更新回款催收记录",
)
async def update_payment_reminder(
    reminder_id: int,
    reminder_data: PaymentReminderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:update")),
):
    """更新回款催收记录。"""
    try:
        reminder = get_or_404(db, PaymentReminder, reminder_id, "回款催收记录不存在")

        update_data = reminder_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reminder, key, value)

        db.commit()
        db.refresh(reminder)

        return ResponseModel(
            code=200,
            message="更新回款催收记录成功",
            data=_payment_reminder_response(reminder),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新回款催收记录失败: {str(e)}")
