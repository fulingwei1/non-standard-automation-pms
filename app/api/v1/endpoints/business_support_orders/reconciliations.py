# -*- coding: utf-8 -*-
"""
商务支持模块 - 客户对账单 API endpoints
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_, text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.business_support import Reconciliation
from app.models.project import Customer
from app.models.user import User
from app.schemas.business_support import (
    ReconciliationCreate,
    ReconciliationResponse,
    ReconciliationUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import _send_department_notification, generate_reconciliation_no

router = APIRouter()


# ==================== 客户对账单 ====================


@router.post("/reconciliations", response_model=ResponseModel[ReconciliationResponse], summary="生成客户对账单")
async def create_reconciliation(
    reconciliation_data: ReconciliationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """生成客户对账单"""
    try:
        # 检查客户是否存在
        customer = db.query(Customer).filter(Customer.id == reconciliation_data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")

        # 生成对账单号
        reconciliation_no = generate_reconciliation_no(db)

        # 计算对账期间的数据
        # 1. 期初余额 = 对账开始日期之前的应收余额
        opening_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as balance
            FROM project_payment_plans
            WHERE project_id IN (
                SELECT id FROM projects WHERE customer_id = :customer_id
            )
            AND planned_date < :period_start
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {
            "customer_id": reconciliation_data.customer_id,
            "period_start": reconciliation_data.period_start.strftime("%Y-%m-%d")
        }).fetchone()
        opening_balance = Decimal(str(opening_result[0])) if opening_result and opening_result[0] else Decimal("0")

        # 2. 本期销售 = 对账期间内签订的合同金额
        period_sales_result = db.execute(text("""
            SELECT COALESCE(SUM(contract_amount), 0) as sales
            FROM contracts
            WHERE customer_id = :customer_id
            AND signed_date >= :period_start
            AND signed_date <= :period_end
            AND status IN ('SIGNED', 'EXECUTING')
        """), {
            "customer_id": reconciliation_data.customer_id,
            "period_start": reconciliation_data.period_start.strftime("%Y-%m-%d"),
            "period_end": reconciliation_data.period_end.strftime("%Y-%m-%d")
        }).fetchone()
        period_sales = Decimal(str(period_sales_result[0])) if period_sales_result and period_sales_result[0] else Decimal("0")

        # 3. 本期回款 = 对账期间内的实际回款金额
        period_receipt_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as receipt
            FROM project_payment_plans
            WHERE project_id IN (
                SELECT id FROM projects WHERE customer_id = :customer_id
            )
            AND planned_date >= :period_start
            AND planned_date <= :period_end
            AND actual_amount > 0
        """), {
            "customer_id": reconciliation_data.customer_id,
            "period_start": reconciliation_data.period_start.strftime("%Y-%m-%d"),
            "period_end": reconciliation_data.period_end.strftime("%Y-%m-%d")
        }).fetchone()
        period_receipt = Decimal(str(period_receipt_result[0])) if period_receipt_result and period_receipt_result[0] else Decimal("0")

        # 4. 期末余额 = 期初余额 + 本期销售 - 本期回款
        closing_balance = opening_balance + period_sales - period_receipt

        # 创建对账单
        reconciliation = Reconciliation(
            reconciliation_no=reconciliation_no,
            customer_id=reconciliation_data.customer_id,
            customer_name=customer.customer_name,
            period_start=reconciliation_data.period_start,
            period_end=reconciliation_data.period_end,
            opening_balance=opening_balance,
            period_sales=period_sales,
            period_receipt=period_receipt,
            closing_balance=closing_balance,
            status="draft",
            remark=reconciliation_data.remark
        )

        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)

        return ResponseModel(
            code=200,
            message="生成客户对账单成功",
            data=ReconciliationResponse(
                id=reconciliation.id,
                reconciliation_no=reconciliation.reconciliation_no,
                customer_id=reconciliation.customer_id,
                customer_name=reconciliation.customer_name,
                period_start=reconciliation.period_start,
                period_end=reconciliation.period_end,
                opening_balance=reconciliation.opening_balance,
                period_sales=reconciliation.period_sales,
                period_receipt=reconciliation.period_receipt,
                closing_balance=reconciliation.closing_balance,
                status=reconciliation.status,
                sent_date=reconciliation.sent_date,
                confirm_date=reconciliation.confirm_date,
                customer_confirmed=reconciliation.customer_confirmed,
                customer_confirm_date=reconciliation.customer_confirm_date,
                customer_difference=reconciliation.customer_difference,
                difference_reason=reconciliation.difference_reason,
                reconciliation_file_id=reconciliation.reconciliation_file_id,
                confirmed_file_id=reconciliation.confirmed_file_id,
                remark=reconciliation.remark,
                created_at=reconciliation.created_at,
                updated_at=reconciliation.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成客户对账单失败: {str(e)}")


@router.get("/reconciliations", response_model=ResponseModel[PaginatedResponse[ReconciliationResponse]], summary="获取客户对账单列表")
async def get_reconciliations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取客户对账单列表"""
    try:
        query = db.query(Reconciliation)

        # 筛选条件
        if customer_id:
            query = query.filter(Reconciliation.customer_id == customer_id)
        if status:
            query = query.filter(Reconciliation.status == status)
        if search:
            query = query.filter(
                or_(
                    Reconciliation.reconciliation_no.like(f"%{search}%"),
                    Reconciliation.customer_name.like(f"%{search}%")
                )
            )

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(Reconciliation.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 转换为响应格式
        reconciliation_list = [
            ReconciliationResponse(
                id=item.id,
                reconciliation_no=item.reconciliation_no,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                period_start=item.period_start,
                period_end=item.period_end,
                opening_balance=item.opening_balance,
                period_sales=item.period_sales,
                period_receipt=item.period_receipt,
                closing_balance=item.closing_balance,
                status=item.status,
                sent_date=item.sent_date,
                confirm_date=item.confirm_date,
                customer_confirmed=item.customer_confirmed,
                customer_confirm_date=item.customer_confirm_date,
                customer_difference=item.customer_difference,
                difference_reason=item.difference_reason,
                reconciliation_file_id=item.reconciliation_file_id,
                confirmed_file_id=item.confirmed_file_id,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]

        return ResponseModel(
            code=200,
            message="获取客户对账单列表成功",
            data=PaginatedResponse(
                items=reconciliation_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户对账单列表失败: {str(e)}")


@router.get("/reconciliations/{reconciliation_id}", response_model=ResponseModel[ReconciliationResponse], summary="获取客户对账单详情")
async def get_reconciliation(
    reconciliation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取客户对账单详情"""
    try:
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
        if not reconciliation:
            raise HTTPException(status_code=404, detail="客户对账单不存在")

        return ResponseModel(
            code=200,
            message="获取客户对账单详情成功",
            data=ReconciliationResponse(
                id=reconciliation.id,
                reconciliation_no=reconciliation.reconciliation_no,
                customer_id=reconciliation.customer_id,
                customer_name=reconciliation.customer_name,
                period_start=reconciliation.period_start,
                period_end=reconciliation.period_end,
                opening_balance=reconciliation.opening_balance,
                period_sales=reconciliation.period_sales,
                period_receipt=reconciliation.period_receipt,
                closing_balance=reconciliation.closing_balance,
                status=reconciliation.status,
                sent_date=reconciliation.sent_date,
                confirm_date=reconciliation.confirm_date,
                customer_confirmed=reconciliation.customer_confirmed,
                customer_confirm_date=reconciliation.customer_confirm_date,
                customer_difference=reconciliation.customer_difference,
                difference_reason=reconciliation.difference_reason,
                reconciliation_file_id=reconciliation.reconciliation_file_id,
                confirmed_file_id=reconciliation.confirmed_file_id,
                remark=reconciliation.remark,
                created_at=reconciliation.created_at,
                updated_at=reconciliation.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户对账单详情失败: {str(e)}")


@router.put("/reconciliations/{reconciliation_id}", response_model=ResponseModel[ReconciliationResponse], summary="更新客户对账单")
async def update_reconciliation(
    reconciliation_id: int,
    reconciliation_data: ReconciliationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新客户对账单"""
    try:
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
        if not reconciliation:
            raise HTTPException(status_code=404, detail="客户对账单不存在")

        # 更新字段
        update_data = reconciliation_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reconciliation, key, value)

        # 如果客户确认，更新确认日期
        if reconciliation_data.customer_confirmed and not reconciliation.customer_confirm_date:
            reconciliation.customer_confirm_date = date.today()
            reconciliation.status = "confirmed"

        db.commit()
        db.refresh(reconciliation)

        return ResponseModel(
            code=200,
            message="更新客户对账单成功",
            data=ReconciliationResponse(
                id=reconciliation.id,
                reconciliation_no=reconciliation.reconciliation_no,
                customer_id=reconciliation.customer_id,
                customer_name=reconciliation.customer_name,
                period_start=reconciliation.period_start,
                period_end=reconciliation.period_end,
                opening_balance=reconciliation.opening_balance,
                period_sales=reconciliation.period_sales,
                period_receipt=reconciliation.period_receipt,
                closing_balance=reconciliation.closing_balance,
                status=reconciliation.status,
                sent_date=reconciliation.sent_date,
                confirm_date=reconciliation.confirm_date,
                customer_confirmed=reconciliation.customer_confirmed,
                customer_confirm_date=reconciliation.customer_confirm_date,
                customer_difference=reconciliation.customer_difference,
                difference_reason=reconciliation.difference_reason,
                reconciliation_file_id=reconciliation.reconciliation_file_id,
                confirmed_file_id=reconciliation.confirmed_file_id,
                remark=reconciliation.remark,
                created_at=reconciliation.created_at,
                updated_at=reconciliation.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新客户对账单失败: {str(e)}")


@router.post("/reconciliations/{reconciliation_id}/send", response_model=ResponseModel, summary="发送对账单")
async def send_reconciliation(
    reconciliation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """发送对账单给客户"""
    try:
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
        if not reconciliation:
            raise HTTPException(status_code=404, detail="客户对账单不存在")

        if reconciliation.status != "draft":
            raise HTTPException(status_code=400, detail="对账单已发送，无法重复发送")

        # 更新状态
        reconciliation.status = "sent"
        reconciliation.sent_date = date.today()

        db.commit()

        # 实际发送对账单通知（邮件、系统消息等）
        # 查找财务部门和销售部门的相关人员发送通知

        # 查找财务部门用户
        finance_users = db.query(User).filter(
            User.department.like("%财务%"),
            User.is_active == True
        ).all()

        # 查找销售部门用户
        sales_users = db.query(User).filter(
            User.department.like("%销售%"),
            User.is_active == True
        ).all()

        # 合并去重
        notified_user_ids = set()
        for user in finance_users + sales_users:
            notified_user_ids.add(user.id)

        # 发送系统通知
        notification_title = f"客户对账单已发送 - {reconciliation.customer_name}"
        notification_content = (
            f"对账单号: {reconciliation.reconciliation_no}\n"
            f"客户名称: {reconciliation.customer_name}\n"
            f"对账期间: {reconciliation.period_start} 至 {reconciliation.period_end}\n"
            f"本期销售额: {float(reconciliation.period_sales):,.2f} 元\n"
            f"本期回款: {float(reconciliation.period_receipt):,.2f} 元\n"
            f"期末应收余额: {float(reconciliation.closing_balance):,.2f} 元\n"
            f"发送日期: {reconciliation.sent_date}"
        )

        for user_id in notified_user_ids:
            _send_department_notification(
                db=db,
                user_id=user_id,
                notification_type="RECONCILIATION_SENT",
                title=notification_title,
                content=notification_content,
                source_type="RECONCILIATION",
                source_id=reconciliation.id,
                priority="NORMAL",
                extra_data={
                    "reconciliation_no": reconciliation.reconciliation_no,
                    "customer_id": reconciliation.customer_id,
                    "customer_name": reconciliation.customer_name,
                    "period_start": str(reconciliation.period_start),
                    "period_end": str(reconciliation.period_end),
                    "closing_balance": float(reconciliation.closing_balance)
                }
            )

        return ResponseModel(
            code=200,
            message=f"发送对账单成功，已通知 {len(notified_user_ids)} 位相关人员"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发送对账单失败: {str(e)}")
