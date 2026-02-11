# -*- coding: utf-8 -*-
"""
研发项目工具函数
"""
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.rd_project import RdCost, RdProject


def generate_project_no(db: Session) -> str:
    """生成研发项目编号：RD-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_project_query = db.query(RdProject)
    max_project_query = apply_like_filter(
        max_project_query,
        RdProject,
        f"RD-{today}-%",
        "project_no",
        use_ilike=False,
    )
    max_project = max_project_query.order_by(desc(RdProject.project_no)).first()
    if max_project:
        seq = int(max_project.project_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RD-{today}-{seq:03d}"


def generate_cost_no(db: Session) -> str:
    """生成研发费用编号：RC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_cost_query = db.query(RdCost)
    max_cost_query = apply_like_filter(
        max_cost_query,
        RdCost,
        f"RC-{today}-%",
        "cost_no",
        use_ilike=False,
    )
    max_cost = max_cost_query.order_by(desc(RdCost.cost_no)).first()
    if max_cost:
        seq = int(max_cost.cost_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"RC-{today}-{seq:03d}"
