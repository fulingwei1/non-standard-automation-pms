# -*- coding: utf-8 -*-
"""
验收单跟踪 - 基础CRUD操作
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.models.acceptance import AcceptanceOrder
from app.models.business_support import AcceptanceTracking
from app.models.project import Project
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import (
    AcceptanceTrackingCreate,
    AcceptanceTrackingResponse,
    AcceptanceTrackingUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .tracking_helpers import build_tracking_response

router = APIRouter()


@router.get("/acceptance-tracking", response_model=ResponseModel[PaginatedResponse[AcceptanceTrackingResponse]], summary="获取验收单跟踪列表")
async def get_acceptance_tracking(
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    tracking_status: Optional[str] = Query(None, description="跟踪状态筛选"),
    condition_check_status: Optional[str] = Query(None, description="验收条件检查状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取验收单跟踪列表（商务支持角度）"""
    try:
        query = db.query(AcceptanceTracking)

        # 筛选条件
        if project_id:
            query = query.filter(AcceptanceTracking.project_id == project_id)
        if customer_id:
            query = query.filter(AcceptanceTracking.customer_id == customer_id)
        if tracking_status:
            query = query.filter(AcceptanceTracking.tracking_status == tracking_status)
        if condition_check_status:
            query = query.filter(AcceptanceTracking.condition_check_status == condition_check_status)

        # 应用关键词过滤（验收单号/客户名称/项目编码）
        query = apply_keyword_filter(query, AcceptanceTracking, search, ["acceptance_order_no", "customer_name", "project_code"])

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(AcceptanceTracking.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        # 转换为响应格式
        tracking_list = [build_tracking_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取验收单跟踪列表成功",
            data=PaginatedResponse(
                items=tracking_list,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验收单跟踪列表失败: {str(e)}")


@router.post("/acceptance-tracking", response_model=ResponseModel[AcceptanceTrackingResponse], summary="创建验收单跟踪记录")
async def create_acceptance_tracking(
    tracking_data: AcceptanceTrackingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建验收单跟踪记录"""
    try:
        # 检查验收单是否存在
        acceptance_order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == tracking_data.acceptance_order_id).first()
        if not acceptance_order:
            raise HTTPException(status_code=404, detail="验收单不存在")

        # 检查是否已有跟踪记录
        existing = db.query(AcceptanceTracking).filter(
            AcceptanceTracking.acceptance_order_id == tracking_data.acceptance_order_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该验收单已有跟踪记录")

        # 获取项目信息
        project = db.query(Project).filter(Project.id == acceptance_order.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取客户信息（从项目获取）
        customer = project.customer if hasattr(project, 'customer') else None
        if not customer:
            # 尝试从合同获取
            if tracking_data.contract_id:
                contract = db.query(Contract).filter(Contract.id == tracking_data.contract_id).first()
                if contract:
                    customer = contract.customer

        if not customer:
            raise HTTPException(status_code=404, detail="无法获取客户信息")

        # 获取业务员信息
        sales_person_id = tracking_data.sales_person_id
        sales_person_name = None
        if sales_person_id:
            sales_person = db.query(User).filter(User.id == sales_person_id).first()
            if sales_person:
                sales_person_name = sales_person.username

        # 获取合同信息
        contract_no = None
        if tracking_data.contract_id:
            contract = db.query(Contract).filter(Contract.id == tracking_data.contract_id).first()
            if contract:
                contract_no = contract.contract_code

        # 创建跟踪记录
        tracking = AcceptanceTracking(
            acceptance_order_id=tracking_data.acceptance_order_id,
            acceptance_order_no=acceptance_order.order_no,
            project_id=acceptance_order.project_id,
            project_code=project.project_code,
            customer_id=customer.id,
            customer_name=customer.customer_name,
            contract_id=tracking_data.contract_id,
            contract_no=contract_no,
            sales_person_id=sales_person_id,
            sales_person_name=sales_person_name,
            support_person_id=current_user.id,
            condition_check_status="pending",
            tracking_status="pending",
            report_status="pending",
            warranty_status="not_started",
            remark=tracking_data.remark
        )

        db.add(tracking)
        db.commit()
        db.refresh(tracking)

        return ResponseModel(
            code=200,
            message="创建验收单跟踪记录成功",
            data=build_tracking_response(tracking)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建验收单跟踪记录失败: {str(e)}")


@router.get("/acceptance-tracking/{tracking_id}", response_model=ResponseModel[AcceptanceTrackingResponse], summary="获取验收单跟踪详情")
async def get_acceptance_tracking_detail(
    tracking_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取验收单跟踪详情"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        return ResponseModel(
            code=200,
            message="获取验收单跟踪详情成功",
            data=build_tracking_response(tracking)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验收单跟踪详情失败: {str(e)}")


@router.put("/acceptance-tracking/{tracking_id}", response_model=ResponseModel[AcceptanceTrackingResponse], summary="更新验收单跟踪记录")
async def update_acceptance_tracking(
    tracking_id: int,
    tracking_data: AcceptanceTrackingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新验收单跟踪记录"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        # 更新字段
        update_data = tracking_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tracking, key, value)

        db.commit()
        db.refresh(tracking)

        return ResponseModel(
            code=200,
            message="更新验收单跟踪记录成功",
            data=build_tracking_response(tracking)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新验收单跟踪记录失败: {str(e)}")
