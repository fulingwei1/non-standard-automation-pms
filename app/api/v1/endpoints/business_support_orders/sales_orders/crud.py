# -*- coding: utf-8 -*-
"""
销售订单管理 - CRUD操作
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.models.business_support import SalesOrder, SalesOrderItem
from app.models.project import Customer
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import SalesOrderCreate, SalesOrderResponse, SalesOrderUpdate
from app.schemas.common import PaginatedResponse, ResponseModel
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

from ..utils import generate_order_no
from .utils import build_sales_order_response

router = APIRouter()


@router.get("/sales-orders", response_model=ResponseModel[PaginatedResponse[SalesOrderResponse]], summary="获取销售订单列表")
async def get_sales_orders(
    pagination: PaginationParams = Depends(get_pagination_query),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    order_status: Optional[str] = Query(None, description="订单状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售订单列表"""
    try:
        query = db.query(SalesOrder)

        # 筛选条件
        if contract_id:
            query = query.filter(SalesOrder.contract_id == contract_id)
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        if project_id:
            query = query.filter(SalesOrder.project_id == project_id)
        if order_status:
            query = query.filter(SalesOrder.order_status == order_status)

        # 使用统一的关键词过滤
        query = apply_keyword_filter(query, SalesOrder, search, ["order_no", "customer_name", "contract_no"])

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(SalesOrder.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        # 转换为响应格式
        order_list = [build_sales_order_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取销售订单列表成功",
            data=PaginatedResponse(
                items=order_list,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售订单列表失败: {str(e)}")


@router.post("/sales-orders", response_model=ResponseModel[SalesOrderResponse], summary="创建销售订单")
async def create_sales_order(
    order_data: SalesOrderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建销售订单"""
    try:
        # 生成订单编号
        order_no = order_data.order_no or generate_order_no(db)

        # 检查订单编号是否已存在
        existing = db.query(SalesOrder).filter(SalesOrder.order_no == order_no).first()
        if existing:
            raise HTTPException(status_code=400, detail="订单编号已存在")

        # 获取客户名称
        customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")

        # 获取合同编号（如果有）
        contract_no = None
        if order_data.contract_id:
            contract = db.query(Contract).filter(Contract.id == order_data.contract_id).first()
            if contract:
                contract_no = contract.contract_code

        # 创建销售订单
        sales_order = SalesOrder(
            order_no=order_no,
            contract_id=order_data.contract_id,
            contract_no=contract_no,
            customer_id=order_data.customer_id,
            customer_name=customer.customer_name,
            project_id=order_data.project_id,
            order_type=order_data.order_type or "standard",
            order_amount=order_data.order_amount,
            currency=order_data.currency or "CNY",
            required_date=order_data.required_date,
            promised_date=order_data.promised_date,
            order_status="draft",
            sales_person_id=order_data.sales_person_id,
            sales_person_name=order_data.sales_person_name,
            support_person_id=current_user.id,
            remark=order_data.remark
        )

        db.add(sales_order)
        db.flush()  # 获取订单ID

        # 创建订单明细
        if order_data.items:
            for item_data in order_data.items:
                order_item = SalesOrderItem(
                    sales_order_id=sales_order.id,
                    item_name=item_data.item_name,
                    item_spec=item_data.item_spec,
                    qty=item_data.qty,
                    unit=item_data.unit,
                    unit_price=item_data.unit_price,
                    amount=item_data.amount,
                    remark=item_data.remark
                )
                db.add(order_item)

        db.commit()
        db.refresh(sales_order)

        return ResponseModel(
            code=200,
            message="创建销售订单成功",
            data=build_sales_order_response(sales_order)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建销售订单失败: {str(e)}")


@router.get("/sales-orders/{order_id}", response_model=ResponseModel[SalesOrderResponse], summary="获取销售订单详情")
async def get_sales_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售订单详情"""
    try:
        sales_order = get_or_404(db, SalesOrder, order_id, "销售订单不存在")

        return ResponseModel(
            code=200,
            message="获取销售订单详情成功",
            data=build_sales_order_response(sales_order)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售订单详情失败: {str(e)}")


@router.put("/sales-orders/{order_id}", response_model=ResponseModel[SalesOrderResponse], summary="更新销售订单")
async def update_sales_order(
    order_id: int,
    order_data: SalesOrderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新销售订单"""
    try:
        sales_order = get_or_404(db, SalesOrder, order_id, "销售订单不存在")

        # 更新字段
        update_data = order_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sales_order, key, value)

        db.commit()
        db.refresh(sales_order)

        return ResponseModel(
            code=200,
            message="更新销售订单成功",
            data=build_sales_order_response(sales_order)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新销售订单失败: {str(e)}")
