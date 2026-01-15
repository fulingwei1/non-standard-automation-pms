# -*- coding: utf-8 -*-
"""
研发费用类型 - 自动生成
从 rd_project.py 拆分
"""

# -*- coding: utf-8 -*-
"""
研发项目管理 API endpoints
包含：研发项目立项、审批、结项、费用归集、报表生成
适用场景：IPO合规、高新技术企业认定、研发费用加计扣除
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core import security
from app.core.config import settings

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents" / "rd_projects"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
from app.models.user import User
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.project import ProjectDocument
from app.models.rd_project import (
    RdProject, RdProjectCategory, RdCost, RdCostType,
    RdCostAllocationRule, RdReportRecord
)
from app.schemas.rd_project import (
    RdProjectCategoryCreate, RdProjectCategoryUpdate, RdProjectCategoryResponse,
    RdProjectCreate, RdProjectUpdate, RdProjectResponse,
    RdProjectApproveRequest, RdProjectCloseRequest, RdProjectLinkRequest,
    RdCostTypeCreate, RdCostTypeResponse,
    RdCostCreate, RdCostUpdate, RdCostResponse,
    RdCostCalculateLaborRequest, RdCostSummaryResponse,
    RdCostAllocationRuleCreate, RdCostAllocationRuleResponse,
    RdReportRecordResponse
)
from app.schemas.timesheet import (
    TimesheetCreate, TimesheetUpdate, TimesheetResponse, TimesheetListResponse
)
from app.schemas.project import (
    ProjectDocumentCreate, ProjectDocumentUpdate, ProjectDocumentResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


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



from fastapi import APIRouter

router = APIRouter(
    prefix="/rd-project/expense-types",
    tags=["expense_types"]
)

# 共 1 个路由

# ==================== 研发费用类型 ====================

@router.get("/rd-cost-types", response_model=ResponseModel)
def get_rd_cost_types(
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="费用大类筛选：LABOR/MATERIAL/DEPRECIATION/OTHER"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    获取研发费用类型列表
    """
    query = db.query(RdCostType)
    
    if category:
        query = query.filter(RdCostType.category == category)
    if is_active is not None:
        query = query.filter(RdCostType.is_active == is_active)
    
    cost_types = query.order_by(RdCostType.sort_order, RdCostType.type_code).all()
    
    return ResponseModel(
        code=200,
        message="success",
        data=[RdCostTypeResponse.model_validate(ct) for ct in cost_types]
    )



