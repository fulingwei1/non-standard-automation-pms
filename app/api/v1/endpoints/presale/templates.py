# -*- coding: utf-8 -*-
"""
方案模板库 - 自动生成
从 presale.py 拆分
"""
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.common.query_filters import apply_keyword_filter, apply_like_filter, apply_pagination
from app.core import security
from app.common.pagination import get_pagination_query, PaginationParams
from app.models.presale import (
    PresaleSolution,
    PresaleSolutionCost,
    PresaleSolutionTemplate,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.presale import (
    SolutionResponse,
    TemplateCreate,
    TemplateResponse,
)

# 使用统一的编码生成工具
from app.utils.domain_codes import presale as presale_codes

generate_ticket_no = presale_codes.generate_ticket_no
generate_solution_no = presale_codes.generate_solution_no
generate_tender_no = presale_codes.generate_tender_no

router = APIRouter(
    prefix="/presale/templates",
    tags=["templates"]
)

# 共 5 个路由

# ==================== 方案模板库 ====================

@router.get("", response_model=PaginatedResponse)
def read_templates(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（模板名称）"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    test_type: Optional[str] = Query(None, description="测试类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    模板列表
    """
    query = db.query(PresaleSolutionTemplate)

    # 应用关键词过滤（模板名称）
    query = apply_keyword_filter(query, PresaleSolutionTemplate, keyword, ["name"])

    if industry:
        query = query.filter(PresaleSolutionTemplate.industry == industry)

    if test_type:
        query = query.filter(PresaleSolutionTemplate.test_type == test_type)

    if is_active is not None:
        query = query.filter(PresaleSolutionTemplate.is_active == is_active)

    total = query.count()
    templates = apply_pagination(query.order_by(desc(PresaleSolutionTemplate.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for template in templates:
        items.append(TemplateResponse(
            id=template.id,
            template_no=template.template_no,
            name=template.name,
            industry=template.industry,
            test_type=template.test_type,
            description=template.description,
            use_count=template.use_count,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
        ))

    return pagination.to_response(items, total)


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: TemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建模板
    """
    # 生成模板编号
    today = datetime.now().strftime("%y%m%d")
    max_template_query = db.query(PresaleSolutionTemplate)
    max_template_query = apply_like_filter(
        max_template_query,
        PresaleSolutionTemplate,
        f"TMP-{today}-%",
        "template_no",
        use_ilike=False,
    )
    max_template = max_template_query.order_by(desc(PresaleSolutionTemplate.template_no)).first()
    if max_template:
        seq = int(max_template.template_no.split("-")[-1]) + 1
    else:
        seq = 1
    template_no = f"TMP-{today}-{seq:03d}"

    template = PresaleSolutionTemplate(
        template_no=template_no,
        name=template_in.name,
        industry=template_in.industry,
        test_type=template_in.test_type,
        description=template_in.description,
        content_template=template_in.content_template,
        cost_template=template_in.cost_template,
        attachments=template_in.attachments,
        is_active=True,
        created_by=current_user.id
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return TemplateResponse(
        id=template.id,
        template_no=template.template_no,
        name=template.name,
        industry=template.industry,
        test_type=template.test_type,
        description=template.description,
        use_count=template.use_count,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/stats", response_model=ResponseModel)
def get_template_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    模板使用统计
    """

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    # 获取所有模板
    templates = db.query(PresaleSolutionTemplate).all()

    template_stats = []
    for template in templates:
        # 统计该模板在此时间段内创建方案的数量
        solutions_query = db.query(PresaleSolution).filter(
            PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
            PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        solutions_query = apply_keyword_filter(
            solutions_query,
            PresaleSolution,
            template.name,
            "solution_overview",
            use_ilike=False,
        )
        solutions_count = solutions_query.count()

        # 计算复用率（使用次数 / 总方案数）
        total_solutions = db.query(PresaleSolution).filter(
            PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
            PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
        ).count()

        reuse_rate = (solutions_count / total_solutions * 100) if total_solutions > 0 else 0.0

        template_stats.append({
            "template_id": template.id,
            "template_no": template.template_no,
            "template_name": template.name,
            "industry": template.industry,
            "test_type": template.test_type,
            "total_use_count": template.use_count or 0,
            "period_use_count": solutions_count,
            "reuse_rate": round(reuse_rate, 2),
            "is_active": template.is_active
        })

    # 按使用次数排序
    template_stats.sort(key=lambda x: x["period_use_count"], reverse=True)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "templates": template_stats,
            "summary": {
                "total_templates": len(templates),
                "active_templates": len([t for t in templates if t.is_active]),
                "total_uses": sum(t["period_use_count"] for t in template_stats),
                "avg_reuse_rate": round(sum(t["reuse_rate"] for t in template_stats) / len(template_stats), 2) if template_stats else 0.0
            }
        }
    )


@router.get("/{template_id}", response_model=TemplateResponse)
def read_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    模板详情
    """
    template = db.query(PresaleSolutionTemplate).filter(PresaleSolutionTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return TemplateResponse(
        id=template.id,
        template_no=template.template_no,
        name=template.name,
        industry=template.industry,
        test_type=template.test_type,
        description=template.description,
        use_count=template.use_count,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/{template_id}/apply", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
def apply_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    ticket_id: Optional[int] = Query(None, description="关联工单ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    opportunity_id: Optional[int] = Query(None, description="商机ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从模板创建方案
    """
    template = db.query(PresaleSolutionTemplate).filter(PresaleSolutionTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已禁用")

    # 创建方案
    solution = PresaleSolution(
        solution_no=generate_solution_no(db),
        name=f"{template.name}（基于模板）",
        solution_type='STANDARD',
        industry=template.industry,
        test_type=template.test_type,
        ticket_id=ticket_id,
        customer_id=customer_id,
        opportunity_id=opportunity_id,
        requirement_summary=template.description,
        solution_overview=template.content_template,
        status='DRAFT',
        version='V1.0',
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username
    )

    db.add(solution)
    db.flush()

    # 如果模板有成本模板，创建成本明细
    if template.cost_template:
        # 解析cost_template JSON并创建PresaleSolutionCost记录
        # cost_template格式：[{"category": "...", "item_name": "...", "unit_price": 100, ...}, ...]
        cost_items = template.cost_template if isinstance(template.cost_template, list) else []
        for item in cost_items:
            cost_record = PresaleSolutionCost(
                solution_id=solution.id,
                category=item.get('category', '其他'),
                item_name=item.get('item_name', ''),
                specification=item.get('specification'),
                unit=item.get('unit'),
                quantity=item.get('quantity'),
                unit_price=item.get('unit_price'),
                amount=item.get('amount')
            )
            db.add(cost_record)

    # 更新模板使用次数
    template.use_count = (template.use_count or 0) + 1
    db.add(template)
    db.commit()
    db.refresh(solution)

    return SolutionResponse(
        id=solution.id,
        solution_no=solution.solution_no,
        name=solution.name,
        solution_type=solution.solution_type,
        industry=solution.industry,
        test_type=solution.test_type,
        ticket_id=solution.ticket_id,
        customer_id=solution.customer_id,
        opportunity_id=solution.opportunity_id,
        requirement_summary=solution.requirement_summary,
        solution_overview=solution.solution_overview,
        technical_spec=solution.technical_spec,
        estimated_cost=float(solution.estimated_cost) if solution.estimated_cost else None,
        suggested_price=float(solution.suggested_price) if solution.suggested_price else None,
        cost_breakdown=solution.cost_breakdown,
        estimated_hours=solution.estimated_hours,
        estimated_duration=solution.estimated_duration,
        status=solution.status,
        version=solution.version,
        parent_id=solution.parent_id,
        reviewer_id=solution.reviewer_id,
        review_time=solution.review_time,
        review_status=solution.review_status,
        review_comment=solution.review_comment,
        created_at=solution.created_at,
        updated_at=solution.updated_at,
    )
