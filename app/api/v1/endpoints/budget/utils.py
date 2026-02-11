# -*- coding: utf-8 -*-
"""
预算工具函数
"""

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.budget import ProjectBudget


def generate_budget_no(db: Session) -> str:
    """生成预算编号：BUD-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_budget_query = db.query(ProjectBudget)
    max_budget_query = apply_like_filter(
        max_budget_query,
        ProjectBudget,
        f"BUD-{today}-%",
        "budget_no",
        use_ilike=False,
    )
    max_budget = max_budget_query.order_by(desc(ProjectBudget.budget_no)).first()

    if max_budget:
        seq = int(max_budget.budget_no.split("-")[-1]) + 1
    else:
        seq = 1

    return f"BUD-{today}-{seq:03d}"


def generate_budget_version(db: Session, project_id: int) -> str:
    """生成预算版本号"""
    max_version = (
        db.query(ProjectBudget)
        .filter(ProjectBudget.project_id == project_id)
        .order_by(desc(ProjectBudget.version))
        .first()
    )

    if max_version:
        # 提取版本号并递增
        version_parts = max_version.version.split('.')
        if len(version_parts) == 2:
            major = int(version_parts[0].replace('V', ''))
            return f"V{major + 1}.0"

    return "V1.0"
