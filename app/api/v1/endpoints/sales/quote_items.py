# -*- coding: utf-8 -*-
"""
报价明细items管理
从 sales/quotes.py 拆分
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.sales import Quote, QuoteItem, QuoteVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import delete_obj, get_or_404, save_obj


def _check_version_scope(db: Session, quote_version_id: int, current_user: User) -> QuoteVersion:
    """加载报价版本，通过父 Quote 检查数据权限"""
    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")
    quote = get_or_404(db, Quote, version.quote_id, detail="报价不存在")
    if not security.check_sales_data_permission(quote, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该报价")
    return version


def _check_item_scope(db: Session, item_id: int, current_user: User) -> QuoteItem:
    """加载报价明细，通过 QuoteVersion -> Quote 检查数据权限"""
    item = get_or_404(db, QuoteItem, item_id, detail="报价明细不存在")
    _check_version_scope(db, item.quote_version_id, current_user)
    return item

router = APIRouter()


@router.get("/quotes/{quote_version_id}/items", response_model=ResponseModel)
def get_quote_items(
    quote_version_id: int,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价版本的明细列表

    Args:
        quote_version_id: 报价版本ID
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前用户

    Returns:
        ResponseModel: 报价明细列表
    """
    try:
        # 验证报价版本存在 + 数据权限
        _check_version_scope(db, quote_version_id, current_user)

        # 查询明细列表
        items = (
            db.query(QuoteItem)
            .filter(QuoteItem.quote_version_id == quote_version_id)
            .order_by(QuoteItem.id)
        )
        items = apply_pagination(items, pagination.offset, pagination.limit).all()

        # 转换为字典列表
        items_data = [
            {
                "id": item.id,
                "quote_version_id": item.quote_version_id,
                "item_type": item.item_type,
                "item_name": item.item_name,
                "qty": float(item.qty) if item.qty else None,
                "unit_price": float(item.unit_price) if item.unit_price else None,
                "cost": float(item.cost) if item.cost else None,
                "lead_time_days": item.lead_time_days,
                "remark": item.remark,
                "cost_category": item.cost_category,
                "cost_source": item.cost_source,
                "specification": item.specification,
                "unit": item.unit,
            }
            for item in items
        ]

        return ResponseModel(code=200, message="报价明细列表获取成功", data=items_data)
    except HTTPException:
        raise
    except Exception as e:
        return ResponseModel(code=500, message=f"获取报价明细失败: {str(e)}")


@router.post("/quotes/{quote_version_id}/items", response_model=ResponseModel)
def create_quote_item(
    quote_version_id: int,
    item_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建报价明细

    Args:
        quote_version_id: 报价版本ID
        item_data: 明细数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    try:
        # 验证报价版本存在 + 数据权限
        _check_version_scope(db, quote_version_id, current_user)

        # 创建明细
        item = QuoteItem(
            quote_version_id=quote_version_id,
            item_type=item_data.get("item_type"),
            item_name=item_data.get("item_name"),
            qty=item_data.get("qty"),
            unit_price=item_data.get("unit_price"),
            cost=item_data.get("cost"),
            lead_time_days=item_data.get("lead_time_days"),
            remark=item_data.get("remark"),
            cost_category=item_data.get("cost_category"),
            cost_source=item_data.get("cost_source", "MANUAL"),
            specification=item_data.get("specification"),
            unit=item_data.get("unit"),
        )
        save_obj(db, item)

        return ResponseModel(code=200, message="报价明细创建成功", data={"id": item.id})
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return ResponseModel(code=500, message=f"创建报价明细失败: {str(e)}")


@router.put("/quotes/items/{item_id}", response_model=ResponseModel)
def update_quote_item(
    item_id: int,
    item_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新报价明细

    Args:
        item_id: 明细ID
        item_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    try:
        item = _check_item_scope(db, item_id, current_user)

        # 更新字段
        for field in [
            "item_type",
            "item_name",
            "qty",
            "unit_price",
            "cost",
            "lead_time_days",
            "remark",
            "cost_category",
            "specification",
            "unit",
        ]:
            if field in item_data:
                setattr(item, field, item_data[field])

        db.commit()
        return ResponseModel(code=200, message="报价明细更新成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return ResponseModel(code=500, message=f"更新报价明细失败: {str(e)}")


@router.delete("/quotes/items/{item_id}", response_model=ResponseModel)
def delete_quote_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除报价明细

    Args:
        item_id: 明细ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    try:
        item = _check_item_scope(db, item_id, current_user)

        delete_obj(db, item)
        return ResponseModel(code=200, message="报价明细删除成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return ResponseModel(code=500, message=f"删除报价明细失败: {str(e)}")
