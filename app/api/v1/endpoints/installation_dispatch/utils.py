# -*- coding: utf-8 -*-
"""
安装调试派工辅助函数
"""

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.installation_dispatch import InstallationDispatchOrder


def generate_order_no(db: Session) -> str:
    """生成安装调试派工单号：IDO-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_order_query = db.query(InstallationDispatchOrder)
    max_order_query = apply_like_filter(
        max_order_query,
        InstallationDispatchOrder,
        f"IDO-{today}-%",
        "order_no",
        use_ilike=False,
    )
    max_order = max_order_query.order_by(desc(InstallationDispatchOrder.order_no)).first()
    if max_order:
        seq = int(max_order.order_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"IDO-{today}-{seq:03d}"
