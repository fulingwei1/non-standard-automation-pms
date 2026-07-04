#!/usr/bin/env python3
"""
验收服务层 - 实施验收→开票自动触发功能
创建日期：2026-01-25
"""
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.acceptance import (
    AcceptanceIssue,
    AcceptanceOrder,
)
from app.models.project.customer import Customer
from app.models.project import (
    Project,
)
from app.models.sales.invoices import Invoice
from app.services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)


class AcceptanceService:
    """验收服务类 - 实施验收→开票自动触发功能"""

    @staticmethod
    async def complete_acceptance_order(
        db: AsyncSession,
        order_id: int,
        completed_by: int,
        completion_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        完成验收单，自动触发开票创建

        Args:
            db: 数据库会话
            order_id: 验收单ID
            completed_by: 完成人ID
            completion_notes: 完成说明

        Returns:
            包含发票ID、发票代码等信息的字典

        Raises:
            ValueError: 如果验收单不存在或状态不正确
        """

        # 1. 查询验收单（包含项目和验收信息）
        result = await db.execute(
            select(AcceptanceOrder, Project, Customer)
            .options(selectinload(Customer))
            .where(AcceptanceOrder.id == order_id)
        )
        order_data = result.first()

        if not order_data:
            raise ValueError(f"验收单不存在: {order_id}")

        order = order_data[0]
        project = order_data[2]
        order_data[3]

        # 2. 检查验收单状态
        if order.status != "PASSED":
            raise ValueError(f"验收单状态不是PASSED: {order.status}")

        # 3. 检查验收单是否有验收问题
        # 如果有未解决的验收问题，不应该触发开票
        issues_result = await db.execute(
            select(AcceptanceIssue).where(
                and_(
                    AcceptanceIssue.acceptance_order_id == order_id,
                    AcceptanceIssue.status == "OPEN",
                )
            )
        )
        open_issues = issues_result.scalars().all()

        if open_issues:
            return {
                "success": False,
                "message": f"存在 {len(open_issues)}个未解决的验收问题，无法触发开票",
                "order_id": order_id,
                "open_issues_count": len(open_issues),
            }

        # 4. 创建发票
        # 使用验收单的总金额作为发票金额
        invoice = Invoice(
            code=await InvoiceService.generate_code(),
            project_id=order.project_id,
            customer_id=order.customer_id,
            contract_id=order.contract_id,
            amount=order.total_amount,
            invoice_type="AUTOMATIC",  # 自动开票
            acceptance_order_id=order.id,
            auto_generated=True,
            status="DRAFT",
        )

        db.add(invoice)
        await db.flush()

        # 5. 更新验收单状态
        order.status = "COMPLETED"
        order.completed_at = datetime.now()
        order.completed_by = completed_by
        order.completion_notes = completion_notes
        order.approved_by = completed_by
        order.approved_at = datetime.now()

        db.add(order)
        await db.commit()

        # 6. 如果验收类型是SAT（现场验收），更新项目状态并移交售后
        if order.acceptance_type == "SAT":
            # SAT验收通过，进入质保阶段
            await AcceptanceService._update_project_to_warranty(db, order.project_id, completed_by)
            # PROJ-23：自动移交售后（质保建档 + 项目/机台质保期回填，幂等）
            await AcceptanceService._handover_to_after_sales(db, order.project_id, completed_by)

        await db.commit()

        # 7. 发送开票通知（模拟）
        # 在实际项目中，这里应该发送邮件或企微通知
        # await _send_invoice_notification(db, invoice, project)

        return {
            "success": True,
            "message": "验收完成，已自动创建发票",
            "order_id": order_id,
            "invoice_id": invoice.id,
            "invoice_code": invoice.code,
            "project_id": order.project_id,
            "project_code": project.code,
        }

    @staticmethod
    async def _update_project_to_warranty(
        db: AsyncSession,
        project_id: int,
        completed_by: int,
    ):
        """更新项目到质保阶段"""

        project = await db.get(Project, project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 阶段推进必须走阶段门；这里仅在项目已通过阶段门进入 S9 后补质保字段。
        if project.stage == "S9" or project.status == "ST30":
            project.stage = "S9"
            project.status = "ST30"
            project.end_date = date.today()
            project.health_status = "H4"  # 已完结
        else:
            logger.warning(
                "验收服务不直接推进项目 %s 至 S9，请先通过阶段门完成 S8→S9",
                project_id,
            )

        db.add(project)
        await db.commit()

    @staticmethod
    async def _handover_to_after_sales(
        db: AsyncSession,
        project_id: int,
        completed_by: int,
    ):
        """SAT 验收通过 → 售后移交（PROJ-23）。

        动作：创建 ACTIVE 质保记录（质保期取项目质保月数，缺省 12 个月）、
        回填项目质保起止日期与机台质保/客户归属（只补空不覆盖）。幂等：
        项目已有 ACTIVE 质保则直接返回既有记录。
        """
        from dateutil.relativedelta import relativedelta
        from sqlalchemy import select as _select

        from app.models.after_sales import AfterSalesWarranty
        from app.models.project import Machine

        project = await db.get(Project, project_id)
        if not project:
            return None

        existing = (
            await db.execute(
                _select(AfterSalesWarranty).where(
                    AfterSalesWarranty.project_id == project_id,
                    AfterSalesWarranty.status == "ACTIVE",
                )
            )
        ).scalars().first()
        if existing:
            return existing

        months = project.warranty_period_months or 12
        start = date.today()
        end = start + relativedelta(months=months)

        warranty = AfterSalesWarranty(
            project_id=project_id,
            customer_id=project.customer_id,
            warranty_no=f"WAR-{project_id}-{start.strftime('%Y%m%d')}",
            warranty_type="STANDARD",
            warranty_start=start,
            warranty_end=end,
            warranty_months=months,
            scope=f"SAT 验收通过自动移交（验收完成人 ID {completed_by}）",
            status="ACTIVE",
        )
        db.add(warranty)

        # 项目质保字段回填（只补空）
        if not project.warranty_period_months:
            project.warranty_period_months = months
        if not project.warranty_start_date:
            project.warranty_start_date = start
        if not project.warranty_end_date:
            project.warranty_end_date = end
        db.add(project)

        # 机台质保/客户归属回填（只补空）
        machines = (
            await db.execute(_select(Machine).where(Machine.project_id == project_id))
        ).scalars().all()
        for machine in machines:
            if not machine.warranty:
                machine.warranty = f"{start.isoformat()} ~ {end.isoformat()}（{months}个月）"
            if not machine.customer_id:
                machine.customer_id = project.customer_id
            db.add(machine)

        await db.commit()
        logger.info(
            "[售后移交] 项目 %s SAT 验收通过：质保 %s（%s~%s），机台 %s 台已回填",
            project_id, warranty.warranty_no, start, end, len(machines),
        )
        return warranty

    @staticmethod
    async def _send_invoice_notification(
        db: AsyncSession,
        invoice: Invoice,
        project: Project,
    ):
        """发送开票通知"""
        # TODO: 完善实现 - 集成通知系统发送开票通知
        logger.info("发送开票通知: 暂未实现 (invoice_id=%s, project_id=%s)", invoice.id, project.id)
