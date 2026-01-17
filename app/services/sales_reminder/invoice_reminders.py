# -*- coding: utf-8 -*-
"""
销售提醒服务 - 发票提醒
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.sales import Contract, Invoice
from app.services.sales_reminder.base import create_notification


def notify_invoice_issued(db: Session, invoice_id: int) -> Optional[Notification]:
    """
    发票开具提醒
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return None

    contract = invoice.contract
    if not contract or not contract.owner_id:
        return None

    return create_notification(
        db=db,
        user_id=contract.owner_id,
        notification_type="INVOICE_ISSUED",
        title=f"发票已开具：{invoice.invoice_code}",
        content=f"发票 {invoice.invoice_code} 已开具，金额：{invoice.total_amount}，请及时跟进收款。",
        source_type="invoice",
        source_id=invoice.id,
        link_url=f"/sales/invoices/{invoice.id}",
        priority="NORMAL",
        extra_data={
            "invoice_code": invoice.invoice_code,
            "invoice_amount": float(invoice.total_amount) if invoice.total_amount else 0,
            "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None
        }
    )
