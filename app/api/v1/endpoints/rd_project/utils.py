# -*- coding: utf-8 -*-
"""
研发项目工具函数
"""
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.rd_project import RdCost, RdProject


def generate_project_no(db: Session) -> str:
    """生成研发项目编号：RD-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_project = (
        db.query(RdProject)
        .filter(RdProject.project_no.like(f"RD-{today}-%"))
        .order_by(desc(RdProject.project_no))
        .first()
    )
    if max_project:
        seq = int(max_project.project_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RD-{today}-{seq:03d}"


def generate_cost_no(db: Session) -> str:
    """生成研发费用编号：RC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_cost = (
        db.query(RdCost)
        .filter(RdCost.cost_no.like(f"RC-{today}-%"))
        .order_by(desc(RdCost.cost_no))
        .first()
    )
    if max_cost:
        seq = int(max_cost.cost_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RC-{today}-{seq:03d}"
