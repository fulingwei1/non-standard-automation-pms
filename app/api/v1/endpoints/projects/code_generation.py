# -*- coding: utf-8 -*-
"""
项目模块 - 编号生成工具函数

包含各种编号生成逻辑
"""

from datetime import date
from sqlalchemy.orm import Session


def generate_review_no(db: Session) -> str:
    """生成复盘编号：REVIEW-YYYYMMDD-XXX"""
    from app.models.project_review import ProjectReview
    today = date.today().strftime("%Y%m%d")
    # 查询当天已有的复盘报告数量
    count = db.query(ProjectReview).filter(
        ProjectReview.review_no.like(f"REVIEW-{today}-%")
    ).count()
    seq = count + 1
    return f"REVIEW-{today}-{seq:03d}"
