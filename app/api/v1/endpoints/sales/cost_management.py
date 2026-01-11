# -*- coding: utf-8 -*-
"""
成本管理 API endpoints

包含成本模板管理和采购物料成本清单管理
"""

from typing import Any, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.sales import (
    QuoteCostTemplate, PurchaseMaterialCost, MaterialCostUpdateReminder
)
from app.schemas.sales import (
    QuoteCostTemplateCreate, QuoteCostTemplateUpdate, QuoteCostTemplateResponse,
    PurchaseMaterialCostCreate, PurchaseMaterialCostUpdate, PurchaseMaterialCostResponse,
    MaterialCostMatchRequest, MaterialCostMatchResponse,
    MaterialCostUpdateReminderResponse, MaterialCostUpdateReminderUpdate
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


# ==================== 报价成本模板管理 ====================


@router.get("/cost-templates", response_model=PaginatedResponse[QuoteCostTemplateResponse])
def get_cost_templates(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    template_type: Optional[str] = Query(None, description="模板类型筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本模板列表
    """
    query = db.query(QuoteCostTemplate)

    if template_type:
        query = query.filter(QuoteCostTemplate.template_type == template_type)
    if equipment_type:
        query = query.filter(QuoteCostTemplate.equipment_type == equipment_type)
    if industry:
        query = query.filter(QuoteCostTemplate.industry == industry)
    if is_active is not None:
        query = query.filter(QuoteCostTemplate.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(desc(QuoteCostTemplate.created_at)).offset(offset).limit(page_size).all()

    items = []
    for template in templates:
        template_dict = {
            **{c.name: getattr(template, c.name) for c in template.__table__.columns},
            "creator_name": template.creator.real_name if template.creator else None
        }
        items.append(QuoteCostTemplateResponse(**template_dict))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/cost-templates/{template_id}", response_model=QuoteCostTemplateResponse)
def get_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本模板详情
    """
    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    template_dict = {
        **{c.name: getattr(template, c.name) for c in template.__table__.columns},
        "creator_name": template.creator.real_name if template.creator else None
    }
    return QuoteCostTemplateResponse(**template_dict)


@router.post("/cost-templates", response_model=QuoteCostTemplateResponse, status_code=201)
def create_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: QuoteCostTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建成本模板
    """
    # 检查模板编码是否已存在
    existing = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    # 计算总成本和分类
    total_cost = Decimal('0')
    categories = set()
    if template_in.cost_structure:
        cost_structure = template_in.cost_structure
        for category in cost_structure.get('categories', []):
            categories.add(category.get('category', ''))
            for item in category.get('items', []):
                qty = Decimal(str(item.get('default_qty', 0)))
                cost = Decimal(str(item.get('default_cost', 0)))
                total_cost += qty * cost

    template_data = template_in.model_dump()
    template_data['total_cost'] = float(total_cost)
    template_data['cost_categories'] = ','.join(categories) if categories else None
    template_data['created_by'] = current_user.id

    template = QuoteCostTemplate(**template_data)
    db.add(template)
    db.commit()
    db.refresh(template)

    template_dict = {
        **{c.name: getattr(template, c.name) for c in template.__table__.columns},
        "creator_name": template.creator.real_name if template.creator else None
    }
    return QuoteCostTemplateResponse(**template_dict)


@router.put("/cost-templates/{template_id}", response_model=QuoteCostTemplateResponse)
def update_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: QuoteCostTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新成本模板
    """
    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    update_data = template_in.model_dump(exclude_unset=True)

    # 如果更新了成本结构，重新计算总成本和分类
    if 'cost_structure' in update_data and update_data['cost_structure']:
        total_cost = Decimal('0')
        categories = set()
        cost_structure = update_data['cost_structure']
        for category in cost_structure.get('categories', []):
            categories.add(category.get('category', ''))
            for item in category.get('items', []):
                qty = Decimal(str(item.get('default_qty', 0)))
                cost = Decimal(str(item.get('default_cost', 0)))
                total_cost += qty * cost
        update_data['total_cost'] = float(total_cost)
        update_data['cost_categories'] = ','.join(categories) if categories else None

    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)

    db.commit()
    db.refresh(template)

    template_dict = {
        **{c.name: getattr(template, c.name) for c in template.__table__.columns},
        "creator_name": template.creator.real_name if template.creator else None
    }
    return QuoteCostTemplateResponse(**template_dict)


@router.delete("/cost-templates/{template_id}", status_code=200)
def delete_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除成本模板
    """
    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    db.delete(template)
    db.commit()

    return ResponseModel(code=200, message="成本模板已删除")


# ==================== 采购物料成本清单管理 ====================


@router.get("/purchase-material-costs", response_model=PaginatedResponse[PurchaseMaterialCostResponse])
def get_purchase_material_costs(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    material_name: Optional[str] = Query(None, description="物料名称搜索"),
    material_type: Optional[str] = Query(None, description="物料类型筛选"),
    is_standard_part: Optional[bool] = Query(None, description="是否标准件"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取采购物料成本清单列表（采购部维护的标准件成本信息）
    """
    query = db.query(PurchaseMaterialCost)

    if material_name:
        query = query.filter(PurchaseMaterialCost.material_name.like(f"%{material_name}%"))
    if material_type:
        query = query.filter(PurchaseMaterialCost.material_type == material_type)
    if is_standard_part is not None:
        query = query.filter(PurchaseMaterialCost.is_standard_part == is_standard_part)
    if is_active is not None:
        query = query.filter(PurchaseMaterialCost.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    costs = query.order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.created_at)).offset(offset).limit(page_size).all()

    items = []
    for cost in costs:
        cost_dict = {
            **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
            "submitter_name": cost.submitter.real_name if cost.submitter else None
        }
        items.append(PurchaseMaterialCostResponse(**cost_dict))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/purchase-material-costs/{cost_id}", response_model=PurchaseMaterialCostResponse)
def get_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取采购物料成本详情
    """
    cost = db.query(PurchaseMaterialCost).filter(PurchaseMaterialCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="采购物料成本不存在")

    cost_dict = {
        **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
        "submitter_name": cost.submitter.real_name if cost.submitter else None
    }
    return PurchaseMaterialCostResponse(**cost_dict)


@router.post("/purchase-material-costs", response_model=PurchaseMaterialCostResponse, status_code=201)
def create_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_in: PurchaseMaterialCostCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建采购物料成本（采购部提交）
    """
    cost = PurchaseMaterialCost(
        **cost_in.model_dump(),
        submitted_by=current_user.id
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)

    cost_dict = {
        **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
        "submitter_name": cost.submitter.real_name if cost.submitter else None
    }
    return PurchaseMaterialCostResponse(**cost_dict)


@router.put("/purchase-material-costs/{cost_id}", response_model=PurchaseMaterialCostResponse)
def update_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    cost_in: PurchaseMaterialCostUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新采购物料成本
    """
    cost = db.query(PurchaseMaterialCost).filter(PurchaseMaterialCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="采购物料成本不存在")

    update_data = cost_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(cost, field):
            setattr(cost, field, value)

    db.add(cost)
    db.commit()
    db.refresh(cost)

    cost_dict = {
        **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
        "submitter_name": cost.submitter.real_name if cost.submitter else None
    }
    return PurchaseMaterialCostResponse(**cost_dict)


@router.delete("/purchase-material-costs/{cost_id}", status_code=200)
def delete_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除采购物料成本
    """
    cost = db.query(PurchaseMaterialCost).filter(PurchaseMaterialCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="采购物料成本不存在")

    db.delete(cost)
    db.commit()

    return ResponseModel(code=200, message="删除成功")


@router.post("/purchase-material-costs/match", response_model=MaterialCostMatchResponse)
def match_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    match_request: MaterialCostMatchRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动匹配物料成本（根据物料名称、规格等匹配历史采购价格）
    """
    # 查询启用的标准件成本清单
    query = db.query(PurchaseMaterialCost).filter(
        PurchaseMaterialCost.is_active == True,
        PurchaseMaterialCost.is_standard_part == True
    )

    # 匹配逻辑：优先精确匹配，其次模糊匹配
    matched_cost = None
    suggestions = []
    match_score = 0

    # 1. 精确匹配物料名称
    exact_match = query.filter(
        PurchaseMaterialCost.material_name == match_request.item_name
    ).order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.purchase_date)).first()

    if exact_match:
        matched_cost = exact_match
        match_score = 100
    else:
        # 2. 模糊匹配物料名称
        name_matches = query.filter(
            PurchaseMaterialCost.material_name.like(f"%{match_request.item_name}%")
        ).order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.purchase_date)).limit(5).all()

        if name_matches:
            matched_cost = name_matches[0]
            match_score = 80
            suggestions = name_matches[1:5] if len(name_matches) > 1 else []
        else:
            # 3. 关键词匹配
            if match_request.item_name:
                keywords = match_request.item_name.split()
                for keyword in keywords:
                    if len(keyword) > 2:  # 只匹配长度大于2的关键词
                        keyword_matches = query.filter(
                            or_(
                                PurchaseMaterialCost.material_name.like(f"%{keyword}%"),
                                PurchaseMaterialCost.match_keywords.like(f"%{keyword}%")
                            )
                        ).order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.usage_count)).limit(5).all()

                        if keyword_matches:
                            matched_cost = keyword_matches[0]
                            match_score = 60
                            suggestions = keyword_matches[1:5] if len(keyword_matches) > 1 else []
                            break

    # 如果匹配成功，更新使用次数
    if matched_cost:
        matched_cost.usage_count = (matched_cost.usage_count or 0) + 1
        matched_cost.last_used_at = datetime.now()
        db.add(matched_cost)
        db.commit()
        db.refresh(matched_cost)

    # 构建响应
    matched_cost_dict = None
    if matched_cost:
        matched_cost_dict = {
            **{c.name: getattr(matched_cost, c.name) for c in matched_cost.__table__.columns},
            "submitter_name": matched_cost.submitter.real_name if matched_cost.submitter else None
        }
        matched_cost_dict = PurchaseMaterialCostResponse(**matched_cost_dict)

    suggestions_list = []
    for sug in suggestions:
        sug_dict = {
            **{c.name: getattr(sug, c.name) for c in sug.__table__.columns},
            "submitter_name": sug.submitter.real_name if sug.submitter else None
        }
        suggestions_list.append(PurchaseMaterialCostResponse(**sug_dict))

    return MaterialCostMatchResponse(
        matched=matched_cost is not None,
        match_score=match_score if matched_cost else None,
        matched_cost=matched_cost_dict,
        suggestions=suggestions_list
    )


# ==================== 物料成本更新提醒 ====================


@router.get("/purchase-material-costs/reminder", response_model=MaterialCostUpdateReminderResponse)
def get_cost_update_reminder(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取物料成本更新提醒配置和状态
    """
    reminder = db.query(MaterialCostUpdateReminder).filter(
        MaterialCostUpdateReminder.is_enabled == True
    ).order_by(desc(MaterialCostUpdateReminder.created_at)).first()

    if not reminder:
        # 创建默认提醒配置
        from datetime import date, timedelta
        reminder = MaterialCostUpdateReminder(
            reminder_type="PERIODIC",
            reminder_interval_days=30,
            next_reminder_date=date.today() + timedelta(days=30),
            is_enabled=True,
            include_standard=True,
            include_non_standard=True,
            notify_roles=["procurement", "procurement_manager", "采购工程师", "采购专员", "采购部经理"],
            reminder_count=0
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

    # 计算距离下次提醒的天数
    from datetime import date
    days_until_next = None
    is_due = False

    if reminder.next_reminder_date:
        today = date.today()
        delta = (reminder.next_reminder_date - today).days
        days_until_next = delta
        is_due = delta <= 0

    reminder_dict = {
        **{c.name: getattr(reminder, c.name) for c in reminder.__table__.columns},
        "days_until_next": days_until_next,
        "is_due": is_due
    }

    return MaterialCostUpdateReminderResponse(**reminder_dict)


@router.put("/purchase-material-costs/reminder", response_model=MaterialCostUpdateReminderResponse)
def update_cost_update_reminder(
    *,
    db: Session = Depends(deps.get_db),
    reminder_in: MaterialCostUpdateReminderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新物料成本更新提醒配置
    """
    reminder = db.query(MaterialCostUpdateReminder).filter(
        MaterialCostUpdateReminder.is_enabled == True
    ).order_by(desc(MaterialCostUpdateReminder.created_at)).first()

    if not reminder:
        from datetime import date, timedelta
        reminder = MaterialCostUpdateReminder(
            reminder_type="PERIODIC",
            reminder_interval_days=30,
            next_reminder_date=date.today() + timedelta(days=30),
            is_enabled=True,
            include_standard=True,
            include_non_standard=True,
            notify_roles=["procurement", "procurement_manager", "采购工程师", "采购专员", "采购部经理"],
            reminder_count=0
        )
        db.add(reminder)

    update_data = reminder_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(reminder, field):
            setattr(reminder, field, value)

    reminder.last_updated_by = current_user.id
    reminder.last_updated_at = datetime.now()

    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # 计算距离下次提醒的天数
    from datetime import date
    days_until_next = None
    is_due = False

    if reminder.next_reminder_date:
        today = date.today()
        delta = (reminder.next_reminder_date - today).days
        days_until_next = delta
        is_due = delta <= 0

    reminder_dict = {
        **{c.name: getattr(reminder, c.name) for c in reminder.__table__.columns},
        "days_until_next": days_until_next,
        "is_due": is_due
    }

    return MaterialCostUpdateReminderResponse(**reminder_dict)


@router.post("/purchase-material-costs/reminder/acknowledge", response_model=ResponseModel)
def acknowledge_cost_update_reminder(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认物料成本更新提醒（标记为已处理，更新下次提醒日期）
    """
    reminder = db.query(MaterialCostUpdateReminder).filter(
        MaterialCostUpdateReminder.is_enabled == True
    ).order_by(desc(MaterialCostUpdateReminder.created_at)).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="提醒配置不存在")

    from datetime import date, timedelta

    # 更新提醒日期
    reminder.last_reminder_date = date.today()
    reminder.next_reminder_date = date.today() + timedelta(days=reminder.reminder_interval_days)
    reminder.reminder_count = (reminder.reminder_count or 0) + 1
    reminder.last_updated_by = current_user.id
    reminder.last_updated_at = datetime.now()

    db.add(reminder)
    db.commit()

    return ResponseModel(
        code=200,
        message="提醒已确认",
        data={
            "next_reminder_date": reminder.next_reminder_date.isoformat(),
            "reminder_count": reminder.reminder_count
        }
    )
