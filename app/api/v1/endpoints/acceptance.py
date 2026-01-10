# -*- coding: utf-8 -*-
"""
验收管理 API endpoints
包含：验收模板、验收单、检查项、问题管理、签字与报告
"""

import os
import hashlib
import logging
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.acceptance import (
    AcceptanceTemplate, TemplateCategory, TemplateCheckItem,
    AcceptanceOrder, AcceptanceOrderItem,
    AcceptanceIssue, IssueFollowUp,
    AcceptanceSignature, AcceptanceReport
)
from app.schemas.acceptance import (
    AcceptanceTemplateCreate, AcceptanceTemplateResponse,
    TemplateCategoryCreate, TemplateCheckItemCreate,
    AcceptanceOrderCreate, AcceptanceOrderUpdate, AcceptanceOrderStart, AcceptanceOrderComplete,
    AcceptanceOrderResponse, AcceptanceOrderListResponse,
    CheckItemResultUpdate, CheckItemResultResponse,
    AcceptanceIssueCreate, AcceptanceIssueUpdate, AcceptanceIssueResponse,
    AcceptanceIssueAssign, AcceptanceIssueResolve, AcceptanceIssueVerify, AcceptanceIssueDefer,
    IssueFollowUpCreate, IssueFollowUpResponse,
    AcceptanceSignatureCreate, AcceptanceSignatureResponse,
    AcceptanceReportGenerateRequest, AcceptanceReportResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


# ==================== 验收约束规则验证 ====================

def validate_acceptance_rules(
    db: Session,
    acceptance_type: str,
    project_id: int,
    machine_id: Optional[int] = None,
    order_id: Optional[int] = None
) -> None:
    """
    验证验收约束规则
    
    规则：
    - AR001: FAT验收必须在设备调试完成后
    - AR002: SAT验收必须在FAT通过后
    - AR003: 终验收必须在所有SAT通过后
    
    Args:
        db: 数据库会话
        acceptance_type: 验收类型（FAT/SAT/FINAL）
        project_id: 项目ID
        machine_id: 设备ID（FAT/SAT需要）
        order_id: 验收单ID（用于更新时检查）
    
    Raises:
        HTTPException: 如果违反约束规则
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if acceptance_type == "FAT":
        # AR001: FAT验收必须在设备调试完成后
        if not machine_id:
            raise HTTPException(status_code=400, detail="FAT验收必须指定设备")
        
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        # 检查设备是否在S5（装配调试）阶段之后
        # S5是装配调试，S6是出厂验收，所以设备应该在S5或S6阶段
        if machine.stage not in ["S5", "S6"]:
            raise HTTPException(
                status_code=400,
                detail=f"设备尚未完成调试，当前阶段：{machine.stage}。FAT验收需要在设备调试完成后（S5阶段）进行"
            )
        
        # 检查项目阶段是否在S6（出厂验收）阶段
        if project.stage not in ["S5", "S6"]:
            raise HTTPException(
                status_code=400,
                detail=f"项目尚未进入调试出厂阶段，当前阶段：{project.stage}。FAT验收需要在S5或S6阶段进行"
            )
    
    elif acceptance_type == "SAT":
        # AR002: SAT验收必须在FAT通过后
        if not machine_id:
            raise HTTPException(status_code=400, detail="SAT验收必须指定设备")
        
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        # 检查该设备是否有通过的FAT验收
        fat_orders = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project_id,
            AcceptanceOrder.machine_id == machine_id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "PASSED"
        ).all()
        
        if not fat_orders:
            raise HTTPException(
                status_code=400,
                detail="SAT验收必须在FAT验收通过后进行。请先完成并通过该设备的FAT验收"
            )
        
        # 检查项目阶段是否在S7或S8阶段（现场安装）
        if project.stage not in ["S7", "S8"]:
            raise HTTPException(
                status_code=400,
                detail=f"项目尚未进入现场安装阶段，当前阶段：{project.stage}。SAT验收需要在S7或S8阶段进行"
            )
    
    elif acceptance_type == "FINAL":
        # AR003: 终验收必须在所有SAT通过后
        # 检查项目中所有设备是否都有通过的SAT验收
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        
        if not machines:
            raise HTTPException(status_code=400, detail="项目中没有设备，无法进行终验收")
        
        for machine in machines:
            # 检查该设备是否有通过的SAT验收
            sat_orders = db.query(AcceptanceOrder).filter(
                AcceptanceOrder.project_id == project_id,
                AcceptanceOrder.machine_id == machine.id,
                AcceptanceOrder.acceptance_type == "SAT",
                AcceptanceOrder.status == "COMPLETED",
                AcceptanceOrder.overall_result == "PASSED"
            ).all()
            
            if not sat_orders:
                raise HTTPException(
                    status_code=400,
                    detail=f"设备 {machine.machine_name} (编码: {machine.machine_code}) 尚未通过SAT验收，无法进行终验收。请先完成所有设备的SAT验收"
                )
        
        # 检查项目阶段是否在S8或S9阶段（验收结项）
        if project.stage not in ["S8", "S9"]:
            raise HTTPException(
                status_code=400,
                detail=f"项目尚未进入验收结项阶段，当前阶段：{project.stage}。终验收需要在S8或S9阶段进行"
            )


def validate_completion_rules(
    db: Session,
    order_id: int
) -> None:
    """
    验证完成验收的约束规则
    
    规则：
    - AR004: 存在未闭环阻塞问题不能通过验收
    - AR005: 必检项全部填写才能完成验收（已在complete_acceptance中实现）
    
    Args:
        db: 数据库会话
        order_id: 验收单ID
    
    Raises:
        HTTPException: 如果违反约束规则
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    # AR004: 检查是否存在未闭环的阻塞问题
    blocking_issues = db.query(AcceptanceIssue).filter(
        AcceptanceIssue.order_id == order_id,
        AcceptanceIssue.is_blocking == True,
        AcceptanceIssue.status.in_(["OPEN", "PROCESSING", "RESOLVED", "DEFERRED"])
    ).all()
    
    # 如果问题状态是RESOLVED，需要检查是否已验证通过
    unresolved_blocking_issues = []
    for issue in blocking_issues:
        if issue.status == "RESOLVED":
            # 已解决的问题需要验证通过才能算闭环
            if issue.verified_result != "VERIFIED":
                unresolved_blocking_issues.append(issue)
        else:
            unresolved_blocking_issues.append(issue)
    
    if unresolved_blocking_issues:
        issue_nos = [issue.issue_no for issue in unresolved_blocking_issues]
        raise HTTPException(
            status_code=400,
            detail=f"存在 {len(unresolved_blocking_issues)} 个未闭环的阻塞问题，无法通过验收。问题编号：{', '.join(issue_nos)}"
        )


def validate_edit_rules(
    db: Session,
    order_id: int
) -> None:
    """
    验证编辑验收单的约束规则
    
    规则：
    - AR006: 客户签字后验收单不可修改
    
    Args:
        db: 数据库会话
        order_id: 验收单ID
    
    Raises:
        HTTPException: 如果违反约束规则
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    # AR006: 检查是否有客户签字
    if order.customer_signed_at or order.customer_signer:
        raise HTTPException(
            status_code=400,
            detail="客户已签字确认，验收单不可修改。如需修改，请联系管理员"
        )
    
    # 检查是否有客户签署文件上传
    if order.is_officially_completed:
        raise HTTPException(
            status_code=400,
            detail="验收单已正式完成（已上传客户签署文件），不可修改"
        )


def generate_order_no(
    db: Session,
    acceptance_type: str,
    project_code: str,
    machine_no: Optional[int] = None
) -> str:
    """
    生成验收单号
    
    规则：
    - FAT验收单：FAT-{项目编号}-{设备序号}-{序号}
      示例：FAT-P2025001-M01-001
    - SAT验收单：SAT-{项目编号}-{设备序号}-{序号}
      示例：SAT-P2025001-M01-001
    - 终验收单：FIN-{项目编号}-{序号}
      示例：FIN-P2025001-001
    """
    # 确定前缀
    if acceptance_type == "FAT":
        prefix = "FAT"
    elif acceptance_type == "SAT":
        prefix = "SAT"
    elif acceptance_type == "FINAL":
        prefix = "FIN"
    else:
        # 兼容旧代码，如果类型未知，使用AC前缀
        prefix = "AC"
    
    # 构建基础编号（不含序号）
    if acceptance_type == "FINAL":
        # 终验收没有设备序号
        base_no = f"{prefix}-{project_code}"
    else:
        # FAT和SAT需要设备序号
        if machine_no is None:
            raise ValueError(f"{acceptance_type}验收单必须提供设备序号")
        machine_seq = f"M{machine_no:02d}"  # M01, M02, ...
        base_no = f"{prefix}-{project_code}-{machine_seq}"
    
    # 查找同类型、同项目、同设备（如果是FAT/SAT）的最大序号
    query = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.order_no.like(f"{base_no}-%")
    )
    
    max_order = query.order_by(desc(AcceptanceOrder.order_no)).first()
    
    if max_order:
        # 提取最后一部分序号
        try:
            seq = int(max_order.order_no.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    
    return f"{base_no}-{seq:03d}"


def generate_issue_no(db: Session, order_no: str) -> str:
    """
    生成问题编号
    
    规则：
    - 验收问题：AI-{验收单号后缀}-{序号}
    - 示例：AI-FAT001-001（如果验收单号是 FAT-P2025001-M01-001）
    
    验收单号后缀提取规则：
    - 提取验收单号的前缀（FAT/SAT/FIN）和最后序号部分（保留3位数字格式）
    - 例如：FAT-P2025001-M01-001 -> FAT001
    - 例如：SAT-P2025001-M01-002 -> SAT002
    - 例如：FIN-P2025001-001 -> FIN001
    """
    # 解析验收单号，提取前缀和最后序号
    parts = order_no.split("-")
    if len(parts) >= 2:
        # 提取前缀（FAT/SAT/FIN）
        prefix = parts[0]
        # 提取最后序号部分（保留原始格式，如001）
        last_part = parts[-1]
        try:
            # 尝试转换为整数再格式化，确保是3位数字
            seq_num = int(last_part)
            suffix = f"{prefix}{seq_num:03d}"  # FAT001, SAT002, FIN001
        except ValueError:
            # 如果最后部分不是数字，使用原始格式
            suffix = f"{prefix}{last_part}"
    else:
        # 如果格式不符合预期，使用简化规则
        # 提取前3个字符作为前缀，最后3个字符作为序号
        if len(order_no) >= 6:
            suffix = f"{order_no[:3]}{order_no[-3:]}"
        else:
            suffix = order_no.replace("-", "")[:8]  # 取前8位
    
    # 查找同验收单的最大问题序号
    pattern = f"AI-{suffix}-%"
    max_issue = (
        db.query(AcceptanceIssue)
        .filter(AcceptanceIssue.issue_no.like(pattern))
        .order_by(desc(AcceptanceIssue.issue_no))
        .first()
    )
    
    if max_issue:
        try:
            seq = int(max_issue.issue_no.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    
    return f"AI-{suffix}-{seq:03d}"


# ==================== 验收模板 ====================

@router.get("/acceptance-templates", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_acceptance_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（编码/名称）"),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收模板列表
    """
    query = db.query(AcceptanceTemplate)
    
    if keyword:
        query = query.filter(
            or_(
                AcceptanceTemplate.template_code.like(f"%{keyword}%"),
                AcceptanceTemplate.template_name.like(f"%{keyword}%"),
            )
        )
    
    if acceptance_type:
        query = query.filter(AcceptanceTemplate.acceptance_type == acceptance_type)
    
    if equipment_type:
        query = query.filter(AcceptanceTemplate.equipment_type == equipment_type)
    
    if is_active is not None:
        query = query.filter(AcceptanceTemplate.is_active == is_active)
    
    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(AcceptanceTemplate.created_at).offset(offset).limit(page_size).all()
    
    items = []
    for template in templates:
        items.append(AcceptanceTemplateResponse(
            id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            acceptance_type=template.acceptance_type,
            equipment_type=template.equipment_type,
            version=template.version,
            is_system=template.is_system,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/acceptance-templates/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
def read_acceptance_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收模板详情（含分类和检查项）
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    # 获取分类
    categories_data = []
    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).order_by(TemplateCategory.sort_order).all()
    for category in categories:
        # 获取检查项
        items_data = []
        items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).order_by(TemplateCheckItem.sort_order).all()
        for item in items:
            items_data.append({
                "id": item.id,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "check_method": item.check_method,
                "acceptance_criteria": item.acceptance_criteria,
                "standard_value": item.standard_value,
                "tolerance_min": item.tolerance_min,
                "tolerance_max": item.tolerance_max,
                "unit": item.unit,
                "is_required": item.is_required,
                "is_key_item": item.is_key_item,
                "sort_order": item.sort_order
            })
        
        categories_data.append({
            "id": category.id,
            "category_code": category.category_code,
            "category_name": category.category_name,
            "weight": float(category.weight) if category.weight else 0,
            "sort_order": category.sort_order,
            "is_required": category.is_required,
            "description": category.description,
            "check_items": items_data
        })
    
    return {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "acceptance_type": template.acceptance_type,
        "equipment_type": template.equipment_type,
        "version": template.version,
        "description": template.description,
        "is_system": template.is_system,
        "is_active": template.is_active,
        "categories": categories_data,
        "created_at": template.created_at,
        "updated_at": template.updated_at
    }


@router.post("/acceptance-templates", response_model=AcceptanceTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: AcceptanceTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收模板
    """
    # 检查编码是否已存在
    existing = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    template = AcceptanceTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        acceptance_type=template_in.acceptance_type,
        equipment_type=template_in.equipment_type,
        version=template_in.version,
        description=template_in.description,
        is_system=False,
        is_active=True,
        created_by=current_user.id
    )
    
    db.add(template)
    db.flush()  # 获取template.id
    
    # 创建分类和检查项
    for cat_in in template_in.categories:
        category = TemplateCategory(
            template_id=template.id,
            category_code=cat_in.category_code,
            category_name=cat_in.category_name,
            weight=cat_in.weight,
            sort_order=cat_in.sort_order,
            is_required=cat_in.is_required,
            description=cat_in.description
        )
        db.add(category)
        db.flush()  # 获取category.id
        
        # 创建检查项
        for item_in in cat_in.check_items:
            item = TemplateCheckItem(
                category_id=category.id,
                item_code=item_in.item_code,
                item_name=item_in.item_name,
                check_method=item_in.check_method,
                acceptance_criteria=item_in.acceptance_criteria,
                standard_value=item_in.standard_value,
                tolerance_min=item_in.tolerance_min,
                tolerance_max=item_in.tolerance_max,
                unit=item_in.unit,
                is_required=item_in.is_required,
                is_key_item=item_in.is_key_item,
                sort_order=item_in.sort_order
            )
            db.add(item)
    
    db.commit()
    db.refresh(template)
    
    return AcceptanceTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        acceptance_type=template.acceptance_type,
        equipment_type=template.equipment_type,
        version=template.version,
        is_system=template.is_system,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.get("/acceptance-templates/{template_id}/items", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_template_items(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取模板检查项列表
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).order_by(TemplateCategory.sort_order).all()
    
    items_data = []
    for category in categories:
        items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).order_by(TemplateCheckItem.sort_order).all()
        for item in items:
            items_data.append({
                "id": item.id,
                "category_id": category.id,
                "category_code": category.category_code,
                "category_name": category.category_name,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "check_method": item.check_method,
                "acceptance_criteria": item.acceptance_criteria,
                "standard_value": item.standard_value,
                "tolerance_min": item.tolerance_min,
                "tolerance_max": item.tolerance_max,
                "unit": item.unit,
                "is_required": item.is_required,
                "is_key_item": item.is_key_item,
                "sort_order": item.sort_order
            })
    
    return items_data


@router.post("/acceptance-templates/{template_id}/items", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_template_items(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    category_id: int = Query(..., description="分类ID"),
    items: List[TemplateCheckItemCreate],
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加模板检查项
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    category = db.query(TemplateCategory).filter(
        TemplateCategory.id == category_id,
        TemplateCategory.template_id == template_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在或不属于该模板")
    
    for item_in in items:
        item = TemplateCheckItem(
            category_id=category_id,
            item_code=item_in.item_code,
            item_name=item_in.item_name,
            check_method=item_in.check_method,
            acceptance_criteria=item_in.acceptance_criteria,
            standard_value=item_in.standard_value,
            tolerance_min=item_in.tolerance_min,
            tolerance_max=item_in.tolerance_max,
            unit=item_in.unit,
            is_required=item_in.is_required,
            is_key_item=item_in.is_key_item,
            sort_order=item_in.sort_order
        )
        db.add(item)
    
    db.commit()
    
    return ResponseModel(message="检查项添加成功")


@router.put("/acceptance-templates/{template_id}", response_model=AcceptanceTemplateResponse, status_code=status.HTTP_200_OK)
def update_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: AcceptanceTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新验收模板
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    # 系统预置模板不能修改
    if template.is_system:
        raise HTTPException(status_code=400, detail="系统预置模板不能修改")
    
    # 检查编码是否已被其他模板使用
    if template_in.template_code != template.template_code:
        existing = db.query(AcceptanceTemplate).filter(
            AcceptanceTemplate.template_code == template_in.template_code,
            AcceptanceTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="模板编码已被使用")
    
    # 更新模板基本信息
    template.template_name = template_in.template_name
    template.acceptance_type = template_in.acceptance_type
    template.equipment_type = template_in.equipment_type
    template.version = template_in.version
    template.description = template_in.description
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return AcceptanceTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        acceptance_type=template.acceptance_type,
        equipment_type=template.equipment_type,
        version=template.version,
        is_system=template.is_system,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.delete("/acceptance-templates/{template_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除验收模板（软删除）
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")
    
    # 系统预置模板不能删除
    if template.is_system:
        raise HTTPException(status_code=400, detail="系统预置模板不能删除")
    
    # 检查是否被使用
    used_count = db.query(AcceptanceOrder).filter(AcceptanceOrder.template_id == template_id).count()
    if used_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"模板已被 {used_count} 个验收单使用，无法删除。建议禁用模板而不是删除"
        )
    
    # 软删除：删除分类和检查项
    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).all()
    for category in categories:
        # 删除检查项
        db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).delete()
        # 删除分类
        db.delete(category)
    
    # 删除模板
    db.delete(template)
    db.commit()
    
    return ResponseModel(message="验收模板已删除")


@router.post("/acceptance-templates/{template_id}/copy", response_model=AcceptanceTemplateResponse, status_code=status.HTTP_201_CREATED)
def copy_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    new_code: str = Query(..., description="新模板编码"),
    new_name: str = Query(..., description="新模板名称"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复制验收模板
    """
    source_template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not source_template:
        raise HTTPException(status_code=404, detail="源模板不存在")
    
    # 检查新编码是否已存在
    existing = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.template_code == new_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    # 创建新模板
    new_template = AcceptanceTemplate(
        template_code=new_code,
        template_name=new_name,
        acceptance_type=source_template.acceptance_type,
        equipment_type=source_template.equipment_type,
        version="1.0",
        description=source_template.description,
        is_system=False,
        is_active=True,
        created_by=current_user.id
    )
    db.add(new_template)
    db.flush()
    
    # 复制分类和检查项
    source_categories = db.query(TemplateCategory).filter(
        TemplateCategory.template_id == template_id
    ).order_by(TemplateCategory.sort_order).all()
    
    for source_category in source_categories:
        # 创建新分类
        new_category = TemplateCategory(
            template_id=new_template.id,
            category_code=source_category.category_code,
            category_name=source_category.category_name,
            weight=source_category.weight,
            sort_order=source_category.sort_order,
            is_required=source_category.is_required,
            description=source_category.description
        )
        db.add(new_category)
        db.flush()
        
        # 复制检查项
        source_items = db.query(TemplateCheckItem).filter(
            TemplateCheckItem.category_id == source_category.id
        ).order_by(TemplateCheckItem.sort_order).all()
        
        for source_item in source_items:
            new_item = TemplateCheckItem(
                category_id=new_category.id,
                item_code=source_item.item_code,
                item_name=source_item.item_name,
                check_method=source_item.check_method,
                acceptance_criteria=source_item.acceptance_criteria,
                standard_value=source_item.standard_value,
                tolerance_min=source_item.tolerance_min,
                tolerance_max=source_item.tolerance_max,
                unit=source_item.unit,
                is_required=source_item.is_required,
                is_key_item=source_item.is_key_item,
                sort_order=source_item.sort_order
            )
            db.add(new_item)
    
    db.commit()
    db.refresh(new_template)
    
    return AcceptanceTemplateResponse(
        id=new_template.id,
        template_code=new_template.template_code,
        template_name=new_template.template_name,
        acceptance_type=new_template.acceptance_type,
        equipment_type=new_template.equipment_type,
        version=new_template.version,
        is_system=new_template.is_system,
        is_active=new_template.is_active,
        created_at=new_template.created_at,
        updated_at=new_template.updated_at
    )


# ==================== 验收单 ====================

@router.get("/acceptance-orders", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_acceptance_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（验收单号）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单列表
    """
    query = db.query(AcceptanceOrder)
    
    if keyword:
        query = query.filter(AcceptanceOrder.order_no.like(f"%{keyword}%"))
    
    if project_id:
        query = query.filter(AcceptanceOrder.project_id == project_id)
    
    if machine_id:
        query = query.filter(AcceptanceOrder.machine_id == machine_id)
    
    if acceptance_type:
        query = query.filter(AcceptanceOrder.acceptance_type == acceptance_type)
    
    if status:
        query = query.filter(AcceptanceOrder.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    orders = query.order_by(desc(AcceptanceOrder.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for order in orders:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        machine = None
        if order.machine_id:
            machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
        
        # 统计开放问题数
        open_issues = db.query(AcceptanceIssue).filter(
            AcceptanceIssue.order_id == order.id,
            AcceptanceIssue.status.in_(["OPEN", "IN_PROGRESS"])
        ).count()
        
        items.append(AcceptanceOrderListResponse(
            id=order.id,
            order_no=order.order_no,
            project_name=project.project_name if project else None,
            machine_name=machine.machine_name if machine else None,
            acceptance_type=order.acceptance_type,
            planned_date=order.planned_date,
            status=order.status,
            overall_result=order.overall_result,
            pass_rate=order.pass_rate or Decimal("0"),
            open_issues=open_issues,
            is_officially_completed=order.is_officially_completed or False,
            created_at=order.created_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/acceptance-orders/{order_id}", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def read_acceptance_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单详情
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
    
    template = None
    if order.template_id:
        template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == order.template_id).first()
    
    return AcceptanceOrderResponse(
        id=order.id,
        order_no=order.order_no,
        project_id=order.project_id,
        project_name=project.project_name if project else None,
        machine_id=order.machine_id,
        machine_name=machine.machine_name if machine else None,
        acceptance_type=order.acceptance_type,
        template_id=order.template_id,
        template_name=template.template_name if template else None,
        planned_date=order.planned_date,
        actual_start_date=order.actual_start_date,
        actual_end_date=order.actual_end_date,
        location=order.location,
        status=order.status,
        total_items=order.total_items or 0,
        passed_items=order.passed_items or 0,
        failed_items=order.failed_items or 0,
        na_items=order.na_items or 0,
        pass_rate=order.pass_rate or Decimal("0"),
        overall_result=order.overall_result,
        conclusion=order.conclusion,
        conditions=order.conditions,
        customer_signed_file_path=order.customer_signed_file_path,
        is_officially_completed=order.is_officially_completed or False,
        officially_completed_at=order.officially_completed_at,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.post("/acceptance-orders", response_model=AcceptanceOrderResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: AcceptanceOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收单(FAT/SAT/FINAL)
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == order_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证机台（如果提供）
    machine = None
    machine_no = None
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine or machine.project_id != order_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")
        machine_no = machine.machine_no
    elif order_in.acceptance_type != "FINAL":
        # FAT和SAT验收必须提供设备
        raise HTTPException(status_code=400, detail=f"{order_in.acceptance_type}验收单必须指定设备")
    
    # 验证验收约束规则（AR001, AR002, AR003）
    validate_acceptance_rules(
        db=db,
        acceptance_type=order_in.acceptance_type,
        project_id=order_in.project_id,
        machine_id=order_in.machine_id
    )
    
    # 验证模板（如果提供）
    template = None
    if order_in.template_id:
        template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == order_in.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="验收模板不存在")
        if template.acceptance_type != order_in.acceptance_type:
            raise HTTPException(status_code=400, detail="模板类型与验收类型不匹配")
    
    # 生成验收单号（符合设计规范）
    order_no = generate_order_no(
        db=db,
        acceptance_type=order_in.acceptance_type,
        project_code=project.project_code,
        machine_no=machine_no
    )
    
    order = AcceptanceOrder(
        order_no=order_no,
        project_id=order_in.project_id,
        machine_id=order_in.machine_id,
        acceptance_type=order_in.acceptance_type,
        template_id=order_in.template_id,
        planned_date=order_in.planned_date,
        location=order_in.location,
        status="DRAFT",
        created_by=current_user.id
    )
    
    db.add(order)
    db.flush()  # 获取order.id
    
    # 如果使用了模板，从模板创建检查项
    if template:
        categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template.id).all()
        item_no = 0
        for category in categories:
            items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).all()
            for item in items:
                item_no += 1
                order_item = AcceptanceOrderItem(
                    order_id=order.id,
                    category_id=category.id,
                    category_code=category.category_code,
                    category_name=category.category_name,
                    item_code=item.item_code,
                    item_name=item.item_name,
                    check_method=item.check_method,
                    acceptance_criteria=item.acceptance_criteria,
                    standard_value=item.standard_value,
                    tolerance_min=item.tolerance_min,
                    tolerance_max=item.tolerance_max,
                    unit=item.unit,
                    is_required=item.is_required,
                    is_key_item=item.is_key_item,
                    sort_order=item.sort_order,
                    result_status="PENDING"
                )
                db.add(order_item)
        
        order.total_items = item_no
        db.add(order)
    
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order.id, db, current_user)


@router.put("/acceptance-orders/{order_id}", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def update_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    order_in: AcceptanceOrderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新验收单
    
    只能更新草稿状态的验收单，且客户签字后不可修改（AR006）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    # AR006: 客户签字后验收单不可修改
    validate_edit_rules(db, order_id)
    
    # 只能更新草稿状态的验收单
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能更新草稿状态的验收单")
    
    # 更新字段
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order_id, db, current_user)


@router.post("/acceptance-orders/{order_id}/submit", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def submit_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交验收单（草稿→待验收）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    # AR006: 客户签字后验收单不可修改
    validate_edit_rules(db, order_id)
    
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的验收单")
    
    if order.total_items == 0:
        raise HTTPException(status_code=400, detail="验收单没有检查项，无法提交")
    
    order.status = "PENDING"
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order_id, db, current_user)


@router.put("/acceptance-orders/{order_id}/start", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def start_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    start_in: AcceptanceOrderStart,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始验收（待验收→验收中）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status not in ["DRAFT", "PENDING"]:
        raise HTTPException(status_code=400, detail="只能开始草稿或待验收状态的验收单")
    
    if order.total_items == 0:
        raise HTTPException(status_code=400, detail="验收单没有检查项，无法开始验收")
    
    order.status = "IN_PROGRESS"
    order.actual_start_date = datetime.now()
    if start_in.location:
        order.location = start_in.location
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order_id, db, current_user)


@router.delete("/acceptance-orders/{order_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除验收单（仅草稿状态）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能删除草稿状态的验收单")
    
    # AR006: 客户签字后验收单不可删除
    validate_edit_rules(db, order_id)
    
    # 删除关联的检查项
    db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order_id).delete()
    
    # 删除关联的问题
    issues = db.query(AcceptanceIssue).filter(AcceptanceIssue.order_id == order_id).all()
    for issue in issues:
        # 删除问题的跟进记录
        db.query(IssueFollowUp).filter(IssueFollowUp.issue_id == issue.id).delete()
    db.query(AcceptanceIssue).filter(AcceptanceIssue.order_id == order_id).delete()
    
    # 删除关联的签字记录
    db.query(AcceptanceSignature).filter(AcceptanceSignature.order_id == order_id).delete()
    
    # 删除关联的报告
    db.query(AcceptanceReport).filter(AcceptanceReport.order_id == order_id).delete()
    
    # 删除验收单
    db.delete(order)
    db.commit()
    
    return ResponseModel(message="验收单已删除")


@router.get("/acceptance-orders/{order_id}/items", response_model=List[CheckItemResultResponse], status_code=status.HTTP_200_OK)
def read_acceptance_order_items(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收检查项列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    items = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order_id).order_by(
        AcceptanceOrderItem.category_code, AcceptanceOrderItem.sort_order
    ).all()
    
    items_data = []
    for item in items:
        checked_by_name = None
        if item.checked_by:
            user = db.query(User).filter(User.id == item.checked_by).first()
            checked_by_name = user.real_name or user.username if user else None
        
        items_data.append(CheckItemResultResponse(
            id=item.id,
            category_code=item.category_code,
            category_name=item.category_name,
            item_code=item.item_code,
            item_name=item.item_name,
            check_method=item.check_method,
            acceptance_criteria=item.acceptance_criteria,
            standard_value=item.standard_value,
            tolerance_min=item.tolerance_min,
            tolerance_max=item.tolerance_max,
            unit=item.unit,
            is_required=item.is_required,
            is_key_item=item.is_key_item,
            result_status=item.result_status,
            actual_value=item.actual_value,
            deviation=item.deviation,
            remark=item.remark,
            checked_by=item.checked_by,
            checked_at=item.checked_at,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return items_data


@router.put("/acceptance-items/{item_id}", response_model=CheckItemResultResponse, status_code=status.HTTP_200_OK)
def update_check_item_result(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    result_in: CheckItemResultUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新检查项结果
    """
    item = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="检查项不存在")
    
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == item.order_id).first()
    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只能更新进行中验收单的检查项")
    
    # 更新检查项结果
    item.result_status = result_in.result_status
    item.actual_value = result_in.actual_value
    item.deviation = result_in.deviation
    item.remark = result_in.remark
    item.checked_by = current_user.id
    item.checked_at = datetime.now()
    
    db.add(item)
    
    # 更新验收单统计（支持有条件通过的权重计算）
    items = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order.id).all()
    passed = len([i for i in items if i.result_status == "PASSED"])
    failed = len([i for i in items if i.result_status == "FAILED"])
    na = len([i for i in items if i.result_status == "NA"])
    conditional = len([i for i in items if i.result_status == "CONDITIONAL"])
    # 不适用(NA)的项不计入总数
    total = len([i for i in items if i.result_status != "PENDING" and i.result_status != "NA"])
    
    order.passed_items = passed
    order.failed_items = failed
    order.na_items = na
    order.total_items = len(items)
    
    # 通过率计算：通过数 + 有条件通过数*0.8
    if total > 0:
        # 有条件通过按0.8权重计算
        effective_passed = passed + conditional * Decimal("0.8")
        order.pass_rate = Decimal(str((effective_passed / total) * 100)).quantize(Decimal("0.01"))
    else:
        order.pass_rate = Decimal("0")
    
    db.add(order)
    db.commit()
    db.refresh(item)
    
    return CheckItemResultResponse(
        id=item.id,
        category_code=item.category_code,
        category_name=item.category_name,
        item_code=item.item_code,
        item_name=item.item_name,
        check_method=item.check_method,
        acceptance_criteria=item.acceptance_criteria,
        standard_value=item.standard_value,
        tolerance_min=item.tolerance_min,
        tolerance_max=item.tolerance_max,
        unit=item.unit,
        is_required=item.is_required,
        is_key_item=item.is_key_item,
        result_status=item.result_status,
        actual_value=item.actual_value,
        deviation=item.deviation,
        remark=item.remark,
        checked_by=item.checked_by,
        checked_at=item.checked_at,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.put("/acceptance-orders/{order_id}/complete", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def complete_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    complete_in: AcceptanceOrderComplete,
    auto_trigger_invoice: bool = Query(True, description="自动触发开票"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成验收（自动触发收款计划开票）
    """
    from app.services.acceptance_completion_service import (
        validate_required_check_items,
        update_acceptance_order_status,
        trigger_invoice_on_acceptance,
        handle_acceptance_status_transition,
        handle_progress_integration,
        check_auto_stage_transition_after_acceptance,
        trigger_warranty_period,
        trigger_bonus_calculation
    )
    
    logger = logging.getLogger(__name__)
    
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只能完成进行中状态的验收单")
    
    # AR005: 检查是否所有必检项都已检查
    validate_required_check_items(db, order_id)
    
    # AR004: 检查是否存在未闭环的阻塞问题
    validate_completion_rules(db, order_id)
    
    # 更新验收单状态
    update_acceptance_order_status(
        db,
        order,
        complete_in.overall_result,
        complete_in.conclusion,
        complete_in.conditions
    )
    
    # Issue 7.4: 如果验收通过，检查是否有绑定的收款计划，自动触发开票
    if auto_trigger_invoice and complete_in.overall_result == "PASSED":
        trigger_invoice_on_acceptance(db, order_id, auto_trigger_invoice)
    
    # Sprint 2.2: 验收管理状态联动（FAT/SAT）
    handle_acceptance_status_transition(db, order, complete_in.overall_result)
    
    # 验收联动：处理验收结果对进度跟踪的影响
    handle_progress_integration(db, order, complete_in.overall_result)
    
    # Issue 1.2: FAT/SAT验收通过后自动触发阶段流转检查
    check_auto_stage_transition_after_acceptance(db, order, complete_in.overall_result)
    
    # AR007: 如果终验收通过，自动触发质保期
    trigger_warranty_period(db, order, complete_in.overall_result)
    
    # 如果验收通过，自动触发奖金计算
    trigger_bonus_calculation(db, order, complete_in.overall_result)
    
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order_id, db, current_user)


# ==================== 验收问题 ====================

def build_issue_response(issue: AcceptanceIssue, db: Session) -> AcceptanceIssueResponse:
    """构建问题响应对象"""
    found_by_name = None
    if issue.found_by:
        user = db.query(User).filter(User.id == issue.found_by).first()
        found_by_name = user.real_name or user.username if user else None
    
    assigned_to_name = None
    if issue.assigned_to:
        user = db.query(User).filter(User.id == issue.assigned_to).first()
        assigned_to_name = user.real_name or user.username if user else None
    
    resolved_by_name = None
    if issue.resolved_by:
        user = db.query(User).filter(User.id == issue.resolved_by).first()
        resolved_by_name = user.real_name or user.username if user else None
    
    verified_by_name = None
    if issue.verified_by:
        user = db.query(User).filter(User.id == issue.verified_by).first()
        verified_by_name = user.real_name or user.username if user else None
    
    return AcceptanceIssueResponse(
        id=issue.id,
        issue_no=issue.issue_no,
        order_id=issue.order_id,
        order_item_id=issue.order_item_id,
        issue_type=issue.issue_type,
        severity=issue.severity,
        title=issue.title,
        description=issue.description,
        found_at=issue.found_at,
        found_by=issue.found_by,
        found_by_name=found_by_name,
        status=issue.status,
        assigned_to=issue.assigned_to,
        assigned_to_name=assigned_to_name,
        due_date=issue.due_date,
        solution=issue.solution,
        resolved_at=issue.resolved_at,
        resolved_by=issue.resolved_by,
        resolved_by_name=resolved_by_name,
        verified_at=issue.verified_at,
        verified_by=issue.verified_by,
        verified_by_name=verified_by_name,
        verified_result=issue.verified_result,
        is_blocking=issue.is_blocking,
        attachments=issue.attachments,
        created_at=issue.created_at,
        updated_at=issue.updated_at
    )


@router.get("/acceptance-issues/{issue_id}", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def read_acceptance_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取问题详情
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    return build_issue_response(issue, db)


@router.get("/acceptance-orders/{order_id}/issues", response_model=List[AcceptanceIssueResponse], status_code=status.HTTP_200_OK)
def read_acceptance_issues(
    order_id: int,
    db: Session = Depends(deps.get_db),
    status: Optional[str] = Query(None, description="问题状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收问题列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    query = db.query(AcceptanceIssue).filter(AcceptanceIssue.order_id == order_id)
    
    if status:
        query = query.filter(AcceptanceIssue.status == status)
    
    issues = query.order_by(desc(AcceptanceIssue.found_at)).all()
    
    items = []
    for issue in issues:
        items.append(build_issue_response(issue, db))
    
    return items


@router.post("/acceptance-orders/{order_id}/issues", response_model=AcceptanceIssueResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    issue_in: AcceptanceIssueCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收问题
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if issue_in.order_id != order_id:
        raise HTTPException(status_code=400, detail="问题所属验收单ID不匹配")
    
    # 验证检查项（如果提供）
    if issue_in.order_item_id:
        item = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.id == issue_in.order_item_id).first()
        if not item or item.order_id != order_id:
            raise HTTPException(status_code=400, detail="检查项不存在或不属于该验收单")
    
    # 生成问题编号（符合设计规范）
    issue_no = generate_issue_no(db, order.order_no)
    
    issue = AcceptanceIssue(
        issue_no=issue_no,
        order_id=order_id,
        order_item_id=issue_in.order_item_id,
        issue_type=issue_in.issue_type,
        severity=issue_in.severity,
        title=issue_in.title,
        description=issue_in.description,
        found_by=current_user.id,
        found_at=datetime.now(),
        status="OPEN",
        assigned_to=issue_in.assigned_to,
        due_date=issue_in.due_date,
        is_blocking=issue_in.is_blocking,
        attachments=issue_in.attachments
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return build_issue_response(issue, db)


@router.put("/acceptance-issues/{issue_id}", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def update_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    issue_in: AcceptanceIssueUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新问题状态
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    update_data = issue_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)
    
    # 如果状态更新为已解决，记录解决时间和解决人
    if issue_in.status == "RESOLVED" and not issue.resolved_at:
        issue.resolved_at = datetime.now()
        issue.resolved_by = current_user.id
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return build_issue_response(issue, db)


@router.put("/acceptance-issues/{issue_id}/close", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def close_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    solution: Optional[str] = Query(None, description="解决方案"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="问题已经关闭")
    
    issue.status = "CLOSED"
    issue.solution = solution
    issue.resolved_at = datetime.now()
    issue.resolved_by = current_user.id
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/assign", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def assign_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    assign_in: AcceptanceIssueAssign,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    指派问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    # 验证被指派人是否存在
    assigned_user = db.query(User).filter(User.id == assign_in.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="被指派人不存在")
    
    # 记录原值
    old_assigned_to = issue.assigned_to
    old_due_date = issue.due_date
    
    # 更新问题
    issue.assigned_to = assign_in.assigned_to
    issue.due_date = assign_in.due_date
    issue.status = "PROCESSING" if issue.status == "OPEN" else issue.status
    
    db.add(issue)
    db.flush()
    
    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="ASSIGN",
        action_content=assign_in.remark or f"问题已指派给 {assigned_user.real_name or assigned_user.username}",
        old_value=str(old_assigned_to) if old_assigned_to else None,
        new_value=str(assign_in.assigned_to),
        created_by=current_user.id
    )
    db.add(follow_up)
    
    db.commit()
    db.refresh(issue)
    
    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/resolve", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def resolve_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    resolve_in: AcceptanceIssueResolve,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    解决问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="问题已经关闭，无法解决")
    
    # 保存旧状态（用于跟进记录）
    old_status = issue.status
    
    # 更新问题
    issue.status = "RESOLVED"
    issue.solution = resolve_in.solution
    issue.resolved_at = datetime.now()
    issue.resolved_by = current_user.id
    if resolve_in.attachments:
        # 合并附件
        if issue.attachments:
            issue.attachments = list(issue.attachments) + resolve_in.attachments
        else:
            issue.attachments = resolve_in.attachments
    
    db.add(issue)
    db.flush()
    
    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="RESOLVE",
        action_content=f"问题已解决：{resolve_in.solution}",
        old_value=old_status,
        new_value="RESOLVED",
        attachments=resolve_in.attachments,
        created_by=current_user.id
    )
    db.add(follow_up)
    
    db.commit()
    db.refresh(issue)
    
    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/verify", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def verify_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    verify_in: AcceptanceIssueVerify,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证问题
    
    验证结果：
    - VERIFIED: 验证通过，问题已解决
    - REJECTED: 验证不通过，问题需要重新处理
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    if issue.status != "RESOLVED":
        raise HTTPException(status_code=400, detail="只能验证已解决的问题")
    
    if verify_in.verified_result not in ["VERIFIED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="验证结果必须是 VERIFIED 或 REJECTED")
    
    # 记录原值
    old_status = issue.status
    old_verified_result = issue.verified_result
    
    # 更新问题
    issue.verified_at = datetime.now()
    issue.verified_by = current_user.id
    issue.verified_result = verify_in.verified_result
    
    if verify_in.verified_result == "VERIFIED":
        # 验证通过，关闭问题
        issue.status = "CLOSED"
    else:
        # 验证不通过，重新打开问题
        issue.status = "OPEN"
        issue.resolved_at = None
        issue.resolved_by = None
    
    db.add(issue)
    db.flush()
    
    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="VERIFY",
        action_content=f"验证结果：{verify_in.verified_result}。{verify_in.remark or ''}",
        old_value=old_verified_result or old_status,
        new_value=verify_in.verified_result,
        created_by=current_user.id
    )
    db.add(follow_up)
    
    db.commit()
    db.refresh(issue)
    
    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/defer", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def defer_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    defer_in: AcceptanceIssueDefer,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    延期问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="已关闭的问题不能延期")
    
    # 记录原值
    old_due_date = issue.due_date
    
    # 更新问题
    issue.due_date = defer_in.new_due_date
    issue.status = "DEFERRED" if issue.status != "DEFERRED" else issue.status
    
    db.add(issue)
    db.flush()
    
    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="STATUS_CHANGE",
        action_content=f"问题延期：{defer_in.reason}。新完成日期：{defer_in.new_due_date}",
        old_value=str(old_due_date) if old_due_date else None,
        new_value=str(defer_in.new_due_date),
        created_by=current_user.id
    )
    db.add(follow_up)
    
    db.commit()
    db.refresh(issue)
    
    return build_issue_response(issue, db)


@router.get("/acceptance-issues/{issue_id}/follow-ups", response_model=List[IssueFollowUpResponse], status_code=status.HTTP_200_OK)
def read_issue_follow_ups(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取问题跟进记录
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    follow_ups = db.query(IssueFollowUp).filter(IssueFollowUp.issue_id == issue_id).order_by(IssueFollowUp.created_at).all()
    
    items = []
    for follow_up in follow_ups:
        created_by_name = None
        if follow_up.created_by:
            user = db.query(User).filter(User.id == follow_up.created_by).first()
            created_by_name = user.real_name or user.username if user else None
        
        items.append(IssueFollowUpResponse(
            id=follow_up.id,
            issue_id=follow_up.issue_id,
            action_type=follow_up.action_type,
            action_content=follow_up.action_content,
            old_value=follow_up.old_value,
            new_value=follow_up.new_value,
            attachments=follow_up.attachments,
            created_by=follow_up.created_by,
            created_by_name=created_by_name,
            created_at=follow_up.created_at
        ))
    
    return items


@router.post("/acceptance-issues/{issue_id}/follow-ups", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_issue_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    follow_up_in: IssueFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加跟进记录
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")
    
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type=follow_up_in.action_type,
        action_content=follow_up_in.action_content,
        attachments=follow_up_in.attachments,
        created_by=current_user.id
    )
    
    db.add(follow_up)
    db.commit()
    
    return ResponseModel(message="跟进记录添加成功")


# ==================== 验收签字 ====================

@router.get("/acceptance-orders/{order_id}/signatures", response_model=List[AcceptanceSignatureResponse], status_code=status.HTTP_200_OK)
def read_acceptance_signatures(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收签字列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    signatures = db.query(AcceptanceSignature).filter(AcceptanceSignature.order_id == order_id).order_by(AcceptanceSignature.signed_at).all()
    
    items = []
    for sig in signatures:
        items.append(AcceptanceSignatureResponse(
            id=sig.id,
            order_id=sig.order_id,
            signer_type=sig.signer_type,
            signer_role=sig.signer_role,
            signer_name=sig.signer_name,
            signer_company=sig.signer_company,
            signed_at=sig.signed_at,
            ip_address=sig.ip_address,
            created_at=sig.created_at,
            updated_at=sig.updated_at
        ))
    
    return items


@router.post("/acceptance-orders/{order_id}/signatures", response_model=AcceptanceSignatureResponse, status_code=status.HTTP_201_CREATED)
def add_acceptance_signature(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    order_id: int,
    signature_in: AcceptanceSignatureCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加签字
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只能为已完成状态的验收单添加签字")
    
    if signature_in.order_id != order_id:
        raise HTTPException(status_code=400, detail="签字所属验收单ID不匹配")
    
    signature = AcceptanceSignature(
        order_id=order_id,
        signer_type=signature_in.signer_type,
        signer_role=signature_in.signer_role,
        signer_name=signature_in.signer_name,
        signer_company=signature_in.signer_company,
        signature_data=signature_in.signature_data,
        signed_at=datetime.now(),
        ip_address=request.client.host if request and request.client else None
    )
    
    # 如果是QA签字，更新验收单
    if signature_in.signer_type == "QA":
        order.qa_signer_id = current_user.id
        order.qa_signed_at = datetime.now()
        db.add(order)
    
    # 如果是客户签字，更新验收单
    if signature_in.signer_type == "CUSTOMER":
        order.customer_signer = signature_in.signer_name
        order.customer_signed_at = datetime.now()
        order.customer_signature = signature_in.signature_data
        db.add(order)
    
    db.add(signature)
    db.commit()
    db.refresh(signature)
    
    return AcceptanceSignatureResponse(
        id=signature.id,
        order_id=signature.order_id,
        signer_type=signature.signer_type,
        signer_role=signature.signer_role,
        signer_name=signature.signer_name,
        signer_company=signature.signer_company,
        signed_at=signature.signed_at,
        ip_address=signature.ip_address,
        created_at=signature.created_at,
        updated_at=signature.updated_at
    )


# ==================== 验收报告 ====================

def generate_report_no(db: Session, report_type: str) -> str:
    """生成报告编号：RPT-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RPT-{today}-"
    max_report = (
        db.query(AcceptanceReport)
        .filter(AcceptanceReport.report_no.like(f"{prefix}%"))
        .order_by(desc(AcceptanceReport.report_no))
        .first()
    )
    if max_report:
        seq = int(max_report.report_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_pdf_report(
    order: AcceptanceOrder,
    db: Session,
    report_no: str,
    version: int,
    current_user: User,
    include_signatures: bool = True
) -> bytes:
    """
    生成PDF格式的验收报告
    
    Args:
        order: 验收单对象
        db: 数据库会话
        report_no: 报告编号
        version: 报告版本号
        current_user: 当前用户
        include_signatures: 是否包含签字信息
    
    Returns:
        PDF文件的字节内容
    """
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PDF生成功能不可用，请安装reportlab库：pip install reportlab"
        )
    
    from app.services.pdf_styles import get_pdf_styles
    from app.services.pdf_content_builders import (
        build_basic_info_section,
        build_statistics_section,
        build_conclusion_section,
        build_issues_section,
        build_signatures_section,
        build_footer_section
    )
    
    # 创建PDF缓冲区
    buffer = BytesIO()
    
    # 创建PDF文档
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 获取样式
    styles = get_pdf_styles()
    
    # 获取项目和设备信息
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
    
    # 构建PDF内容
    story = []
    
    # 基本信息部分
    story.extend(build_basic_info_section(order, project, machine, report_no, version, styles))
    
    # 验收项目统计部分
    story.extend(build_statistics_section(order, db, styles))
    
    # 验收结论部分
    story.extend(build_conclusion_section(order, styles))
    
    # 验收问题部分
    story.extend(build_issues_section(order, db, styles))
    
    # 签字信息部分
    if include_signatures:
        story.extend(build_signatures_section(order, db, styles))
    
    # 页脚部分
    story.extend(build_footer_section(current_user, styles))
    
    # 构建PDF
    doc.build(story)
    
    # 获取PDF字节
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


@router.post("/acceptance-orders/{order_id}/report", response_model=AcceptanceReportResponse, status_code=status.HTTP_201_CREATED)
def generate_acceptance_report(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    report_in: AcceptanceReportGenerateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成验收报告
    """
    from app.services.acceptance_report_service import (
        generate_report_no,
        get_report_version,
        build_report_content,
        save_report_file
    )
    
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只有已完成的验收单才能生成报告")
    
    # 生成报告编号和版本
    report_no = generate_report_no(db, report_in.report_type)
    version = get_report_version(db, order_id, report_in.report_type)
    
    # 构建报告内容
    report_content = build_report_content(db, order, report_no, version, current_user)
    
    # 保存报告文件
    file_rel_path, file_size, file_hash = save_report_file(
        report_content, report_no, report_in.report_type,
        report_in.include_signatures, order, db, current_user
    )
    
    # 创建报告记录
    report = AcceptanceReport(
        order_id=order_id,
        report_no=report_no,
        report_type=report_in.report_type,
        version=version,
        report_content=report_content,
        file_path=file_rel_path,
        file_size=file_size,
        file_hash=file_hash,
        generated_at=datetime.now(),
        generated_by=current_user.id
    )
    
    db.add(report)
    
    # 更新验收单的报告文件路径（如果有最新报告）
    if not order.report_file_path or report_in.report_type == "FINAL":
        order.report_file_path = file_rel_path
        db.add(order)
    
    db.commit()
    db.refresh(report)
    
    return AcceptanceReportResponse(
        id=report.id,
        order_id=report.order_id,
        report_no=report.report_no,
        report_type=report.report_type,
        version=report.version,
        report_content=report.report_content,
        file_path=report.file_path,
        file_size=report.file_size,
        file_hash=report.file_hash,
        generated_at=report.generated_at,
        generated_by=report.generated_by,
        generated_by_name=current_user.real_name or current_user.username,
        created_at=report.created_at,
        updated_at=report.updated_at
    )


@router.get("/acceptance-reports/{report_id}/download", response_class=FileResponse)
def download_acceptance_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载验收报告（支持PDF和文本格式）
    """
    report = db.query(AcceptanceReport).filter(AcceptanceReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="验收报告不存在")
    
    if not report.file_path:
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    file_path = os.path.join(settings.UPLOAD_DIR, report.file_path)
    
    if not os.path.exists(file_path):
        # 如果文件不存在，返回报告内容作为文本
        content = report.report_content or "报告内容为空"
        return Response(
            content=content.encode('utf-8'),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={report.report_no}.txt"
            }
        )
    
    filename = os.path.basename(file_path)
    # 根据文件扩展名设置媒体类型
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".txt"):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@router.get("/acceptance-orders/{order_id}/report", response_model=List[AcceptanceReportResponse], status_code=status.HTTP_200_OK)
def read_acceptance_reports(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单的所有报告列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    reports = db.query(AcceptanceReport).filter(
        AcceptanceReport.order_id == order_id
    ).order_by(desc(AcceptanceReport.version)).all()
    
    items = []
    for report in reports:
        generated_by_name = None
        if report.generated_by:
            user = db.query(User).filter(User.id == report.generated_by).first()
            generated_by_name = user.real_name or user.username if user else None
        
        items.append(AcceptanceReportResponse(
            id=report.id,
            order_id=report.order_id,
            report_no=report.report_no,
            report_type=report.report_type,
            version=report.version,
            report_content=report.report_content,
            file_path=report.file_path,
            file_size=report.file_size,
            file_hash=report.file_hash,
            generated_at=report.generated_at,
            generated_by=report.generated_by,
            generated_by_name=generated_by_name,
            created_at=report.created_at,
            updated_at=report.updated_at
        ))
    
    return items


# ==================== 客户签署验收单上传 ====================

@router.post("/acceptance-orders/{order_id}/upload-signed-document", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
async def upload_customer_signed_document(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    file: UploadFile = File(..., description="客户签署的验收单文件"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上传客户签署的验收单文件
    
    上传后，验收单将被标记为正式完成（is_officially_completed=True）
    只有状态为COMPLETED且验收结果为PASSED的验收单才能上传签署文件
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    # 验证验收单状态
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只有已完成状态的验收单才能上传客户签署文件")
    
    if order.overall_result != "PASSED":
        raise HTTPException(status_code=400, detail="只有验收通过的验收单才能上传客户签署文件")
    
    # 验证项目关联
    project = db.query(Project).filter(Project.id == order.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="关联的项目不存在")
    
    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, "acceptance_signed_documents")
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    import uuid
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    unique_filename = f"{order.order_no}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # 保存文件
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 计算相对路径（相对于UPLOAD_DIR）
    relative_path = os.path.relpath(file_path, settings.UPLOAD_DIR)
    
    # 更新验收单
    order.customer_signed_file_path = relative_path
    order.is_officially_completed = True
    order.officially_completed_at = datetime.now()
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_acceptance_order(order_id, db, current_user)


@router.get("/acceptance-orders/{order_id}/download-signed-document", response_class=FileResponse)
def download_customer_signed_document(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载客户签署的验收单文件
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    if not order.customer_signed_file_path:
        raise HTTPException(status_code=404, detail="客户签署文件不存在")
    
    file_path = os.path.join(settings.UPLOAD_DIR, order.customer_signed_file_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    filename = os.path.basename(file_path)
    media_type = "application/pdf" if filename.endswith(".pdf") else "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


# ==================== 手动触发奖金计算 ====================

@router.post("/acceptance-orders/{order_id}/trigger-bonus-calculation", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def trigger_bonus_calculation(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    手动触发验收单关联的奖金计算
    
    只有正式完成的验收单（已上传客户签署文件）才能触发奖金计算
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    # 验证验收单状态
    if not order.is_officially_completed:
        raise HTTPException(status_code=400, detail="只有正式完成的验收单（已上传客户签署文件）才能触发奖金计算")
    
    if order.overall_result != "PASSED":
        raise HTTPException(status_code=400, detail="只有验收通过的验收单才能触发奖金计算")
    
    # 获取项目信息
    project = db.query(Project).filter(Project.id == order.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="关联的项目不存在")
    
    try:
        from app.services.bonus_calculator import BonusCalculator
        calculator = BonusCalculator(db)
        
        # 触发奖金计算
        calculations = calculator.trigger_acceptance_bonus_calculation(project, order)
        
        db.commit()
        
        return ResponseModel(
            code=200,
            message="奖金计算触发成功",
            data={
                "order_id": order_id,
                "order_no": order.order_no,
                "project_id": project.id,
                "project_name": project.project_name,
                "calculations_count": len(calculations),
                "calculations": [
                    {
                        "id": calc.id,
                        "calculation_code": calc.calculation_code,
                        "user_id": calc.user_id,
                        "calculated_amount": float(calc.calculated_amount) if calc.calculated_amount else 0,
                        "status": calc.status,
                    }
                    for calc in calculations
                ] if calculations else []
            }
        )
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"奖金计算失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"奖金计算失败: {str(e)}")
