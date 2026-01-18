# -*- coding: utf-8 -*-
"""
缺料统计 - 缺料看板
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.shortage import (
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageReport,
)
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/shortage/dashboard", response_model=ResponseModel)
def get_shortage_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料看板
    """
    # 统计缺料上报
    total_reports = db.query(ShortageReport).count()
    reported = db.query(ShortageReport).filter(ShortageReport.status == 'REPORTED').count()
    confirmed = db.query(ShortageReport).filter(ShortageReport.status == 'CONFIRMED').count()
    handling = db.query(ShortageReport).filter(ShortageReport.status == 'HANDLING').count()
    resolved = db.query(ShortageReport).filter(ShortageReport.status == 'RESOLVED').count()

    # 统计紧急缺料
    urgent_reports = db.query(ShortageReport).filter(
        ShortageReport.urgent_level.in_(['URGENT', 'CRITICAL']),
        ShortageReport.status != 'RESOLVED'
    ).count()

    # 统计到货跟踪
    total_arrivals = db.query(MaterialArrival).count()
    pending_arrivals = db.query(MaterialArrival).filter(MaterialArrival.status == 'PENDING').count()
    delayed_arrivals = db.query(MaterialArrival).filter(MaterialArrival.is_delayed == True).count()

    # 统计物料替代
    total_substitutions = db.query(MaterialSubstitution).count()
    pending_substitutions = db.query(MaterialSubstitution).filter(
        MaterialSubstitution.status.in_(['DRAFT', 'TECH_PENDING', 'PROD_PENDING'])
    ).count()

    # 统计物料调拨
    total_transfers = db.query(MaterialTransfer).count()
    pending_transfers = db.query(MaterialTransfer).filter(
        MaterialTransfer.status.in_(['DRAFT', 'PENDING'])
    ).count()

    # 最近缺料上报
    recent_reports = db.query(ShortageReport).order_by(desc(ShortageReport.created_at)).limit(10).all()
    recent_reports_list = []
    for report in recent_reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        recent_reports_list.append({
            'id': report.id,
            'report_no': report.report_no,
            'project_name': project.project_name if project else None,
            'material_name': report.material_name,
            'shortage_qty': float(report.shortage_qty),
            'urgent_level': report.urgent_level,
            'status': report.status,
            'report_time': report.report_time
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "reports": {
                "total": total_reports,
                "reported": reported,
                "confirmed": confirmed,
                "handling": handling,
                "resolved": resolved,
                "urgent": urgent_reports
            },
            "arrivals": {
                "total": total_arrivals,
                "pending": pending_arrivals,
                "delayed": delayed_arrivals
            },
            "substitutions": {
                "total": total_substitutions,
                "pending": pending_substitutions
            },
            "transfers": {
                "total": total_transfers,
                "pending": pending_transfers
            },
            "recent_reports": recent_reports_list
        }
    )
