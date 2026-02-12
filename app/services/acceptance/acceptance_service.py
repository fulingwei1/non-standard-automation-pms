#!/usr/bin/env python3
"""
验收服务层 - 实施验收→开票自动触发功能
创建日期：2026-01-25
"""
import logging

from datetime import date, datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acceptance import (
    AcceptanceOrder,
    AcceptanceIssue,
)
from app.models.project import (
    Project,
)
from app.models.sales.invoices import Invoice

from sqlalchemy.orm import selectinload
from app.models.customer import Customer
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
            select(AcceptanceIssue)
            .where(
                and_(
                    AcceptanceIssue.acceptance_order_id == order_id,
                    AcceptanceIssue.status == "OPEN"
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
        
        # 6. 如果验收类型是SAT（现场验收），更新项目状态
        if order.acceptance_type == "SAT":
            # SAT验收通过，进入质保阶段
            await AcceptanceService._update_project_to_warranty(db, order.project_id, completed_by)
        
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
        
        # 进入质保阶段
        if project.stage == "S8" or project.status == "ST08":
            project.stage = "S9"  # 质保结项
            project.status = "ST30"  # 已完结
            project.end_date = date.today()
            project.health_status = "H4"  # 已完结
        
        db.add(project)
        await db.commit()

    @staticmethod
    async def _send_invoice_notification(
        db: AsyncSession,
        invoice: Invoice,
        project: Project,
    ):
        """发送开票通知"""
        # TODO: 完善实现 - 集成通知系统发送开票通知
        logger.info("发送开票通知: 暂未实现 (invoice_id=%s, project_id=%s)",
                     invoice.id, project.id)
