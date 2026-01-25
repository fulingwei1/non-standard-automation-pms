# -*- coding: utf-8 -*-
"""
项目里程碑 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Path, Depends, Query, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.enums import InvoiceStatusEnum
from app.models.project import ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)


def filter_by_status(query, milestone_status: str):
    """自定义状态筛选器"""
    return query.filter(ProjectMilestone.status == milestone_status)


# 使用项目中心CRUD路由基类创建路由
base_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id",
    keyword_fields=["milestone_name", "milestone_code", "description"],
    default_order_by="planned_date",
    default_order_direction="desc",
    custom_filters={
        "status": filter_by_status  # 支持 ?status=PENDING 筛选
    }
)

# 创建新的router，添加扩展端点
router = APIRouter()


# ============================================================
# 扩展端点（从全局端点迁移）
# ============================================================

@router.put("/{milestone_id}/complete", response_model=MilestoneResponse)
def complete_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    actual_date: Optional[str] = Query(None, description="实际完成日期（YYYY-MM-DD）"),
    auto_trigger_invoice: bool = Query(True, description="自动触发开票"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> Any:
    """
    完成里程碑（自动触发收款计划开票）

    - 验证里程碑完成条件（交付物、验收）
    - 更新状态为已完成
    - 自动触发关联的收款计划开票
    """
    import logging
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id,
    ).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    # 验收联动：检查里程碑完成条件（交付物、验收）
    try:
        from app.services.progress_integration_service import ProgressIntegrationService
        integration_service = ProgressIntegrationService(db)
        can_complete, missing_items = integration_service.check_milestone_completion_requirements(milestone)

        if not can_complete:
            raise HTTPException(
                status_code=400,
                detail=f"里程碑不满足完成条件：{', '.join(missing_items)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        # 检查失败时，记录日志但允许完成（向后兼容）
        logger = logging.getLogger(__name__)
        logger.error(f"检查里程碑完成条件失败: {str(e)}", exc_info=True)

    # 更新状态为已完成
    milestone.status = "COMPLETED"

    # 设置实际完成日期
    if actual_date:
        try:
            milestone.actual_date = datetime.strptime(actual_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    elif not milestone.actual_date:
        milestone.actual_date = date.today()

    db.add(milestone)
    db.flush()

    # 检查是否有绑定的收款计划，自动触发开票
    if auto_trigger_invoice:
        payment_plans = db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.milestone_id == milestone_id,
            ProjectPaymentPlan.status == "PENDING"
        ).all()

        for plan in payment_plans:
            # 检查是否已开票
            if plan.invoice_id:
                continue

            # 获取合同信息
            contract = None
            if plan.contract_id:
                contract = db.query(Contract).filter(Contract.id == plan.contract_id).first()

            if contract:
                # 自动创建发票
                today = datetime.now()
                month_str = today.strftime("%y%m%d")
                prefix = f"INV-{month_str}-"
                max_invoice = (
                    db.query(Invoice)
                    .filter(Invoice.invoice_code.like(f"{prefix}%"))
                    .order_by(desc(Invoice.invoice_code))
                    .first()
                )
                if max_invoice:
                    try:
                        seq = int(max_invoice.invoice_code.split("-")[-1]) + 1
                    except (ValueError, TypeError, IndexError):
                        seq = 1
                else:
                    seq = 1
                invoice_code = f"{prefix}{seq:03d}"

                invoice = Invoice(
                    invoice_code=invoice_code,
                    contract_id=contract.id,
                    project_id=plan.project_id,
                    payment_id=None,
                    invoice_type="NORMAL",
                    amount=plan.planned_amount,
                    tax_rate=Decimal("13"),
                    tax_amount=plan.planned_amount * Decimal("13") / Decimal("100"),
                    total_amount=plan.planned_amount * Decimal("113") / Decimal("100"),
                    status=InvoiceStatusEnum.DRAFT,
                    payment_status="PENDING",
                    issue_date=date.today(),
                    due_date=date.today() + timedelta(days=30),
                    buyer_name=contract.customer.customer_name if contract.customer else None,
                    buyer_tax_no=contract.customer.tax_no if contract.customer else None,
                )
                db.add(invoice)
                db.flush()

                # 更新收款计划
                plan.invoice_id = invoice.id
                plan.invoice_no = invoice_code
                plan.invoice_date = date.today()
                plan.invoice_amount = invoice.total_amount
                plan.status = "INVOICED"
                db.add(plan)

    db.commit()
    db.refresh(milestone)
    return milestone


# 从基类router中复制所有端点
for route in base_router.routes:
    router.routes.append(route)
