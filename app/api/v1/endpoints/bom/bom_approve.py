# -*- coding: utf-8 -*-
"""
BOM管理端点 - BOM审核通过后自动创建采购订单
创建日期：2026-01-25
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.material.bom_service import BOMService
from app.api.deps import get_db
from app.core.security import require_permission
from app.models.user import User


router = APIRouter(prefix="/bom/headers", tags=["bom"])


@router.post("/{bom_id}/approve")
async def approve_bom(
    bom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("bom:approve")),
):
    """
    BOM审核通过，自动创建采购订单
    
    功能说明：
    1. 验证BOM存在且状态为APPROVED
    2. 调用BOMService.approve_bom_and_create_purchase_orders()
    3. 返回创建的采购订单数量和ID列表
    
    Args:
        bom_id: BOM ID
        db: 数据库会话
        current_user: 当前用户
            
    Returns:
        包含采购订单数量、采购订单ID列表、采购订单详情的字典
            
    Raises:
        HTTPException: 如果BOM不存在或状态不正确
        """
    
    try:
        result = await BOMService.approve_bom_and_create_purchase_orders(
            db=db,
            bom_id=bom_id,
            approved_by=current_user.id
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"BOM审核通过，已创建 {result['purchase_orders_count']}个采购订单",
            "bom_id": bom_id,
            "purchase_orders_count": result["purchase_orders_count"],
            "purchase_order_ids": result["purchase_order_ids"],
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"BOM审核失败：{str(e)}"
        )
