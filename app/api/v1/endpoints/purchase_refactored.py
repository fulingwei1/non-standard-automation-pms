# -*- coding: utf-8 -*-
"""
采购管理 API endpoints (重构版)
"""

import logging
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.common import Response
from app.services.purchase.purchase_service import PurchaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Response[List[dict]])
def get_purchase_orders(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取采购订单列表
    """
    try:
        service = PurchaseService(db)
        orders = service.get_purchase_orders(
            skip=skip,
            limit=limit,
            project_id=project_id,
            supplier_id=supplier_id,
            status=status
        )
        
        # 转换为响应格式
        order_list = [
            {
                "id": order.id,
                "order_code": order.order_code,
                "supplier_id": order.supplier_id,
                "project_id": order.project_id,
                "total_amount": float(order.total_amount or 0),
                "status": order.status,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            for order in orders
        ]
        
        return Response.success(data=order_list, message="采购订单列表获取成功")
    except Exception as e:
        logger.error(f"获取采购订单失败: {str(e)}")
        return Response.error(message=f"获取采购订单失败: {str(e)}")


@router.get("/{order_id}", response_model=Response[dict])
def get_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取采购订单详情
    """
    try:
        service = PurchaseService(db)
        order = service.get_purchase_order_by_id(order_id)
        
        if not order:
            return Response.error(message="采购订单不存在", code=404)
        
        order_data = {
            "id": order.id,
            "order_code": order.order_code,
            "supplier_id": order.supplier_id,
            "project_id": order.project_id,
            "total_amount": float(order.total_amount or 0),
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
        
        return Response.success(data=order_data, message="采购订单详情获取成功")
    except Exception as e:
        logger.error(f"获取采购订单详情失败: {str(e)}")
        return Response.error(message=f"获取采购订单详情失败: {str(e)}")


@router.post("/", response_model=Response[dict])
def create_purchase_order(
    order_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建采购订单
    """
    try:
        service = PurchaseService(db)
        order = service.create_purchase_order(order_data)
        
        result_data = {
            "id": order.id,
            "order_code": order.order_code,
            "status": order.status
        }
        
        return Response.success(data=result_data, message="采购订单创建成功")
    except Exception as e:
        logger.error(f"创建采购订单失败: {str(e)}")
        return Response.error(message=f"创建采购订单失败: {str(e)}")


@router.put("/{order_id}/submit", response_model=Response[str])
def submit_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    提交采购订单
    """
    try:
        service = PurchaseService(db)
        success = service.submit_purchase_order(order_id)
        
        if success:
            return Response.success(message="采购订单提交成功")
        else:
            return Response.error(message="采购订单不存在", code=404)
    except Exception as e:
        logger.error(f"提交采购订单失败: {str(e)}")
        return Response.error(message=f"提交采购订单失败: {str(e)}")


@router.put("/{order_id}/approve", response_model=Response[str])
def approve_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    审批采购订单
    """
    try:
        service = PurchaseService(db)
        success = service.approve_purchase_order(order_id, current_user.id)
        
        if success:
            return Response.success(message="采购订单审批成功")
        else:
            return Response.error(message="采购订单不存在", code=404)
    except Exception as e:
        logger.error(f"审批采购订单失败: {str(e)}")
        return Response.error(message=f"审批采购订单失败: {str(e)}")


@router.get("/goods-receipts/", response_model=Response[List[dict]])
def get_goods_receipts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    order_id: Optional[int] = Query(None, description="订单ID"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取收货记录列表
    """
    try:
        service = PurchaseService(db)
        receipts = service.get_goods_receipts(
            skip=skip,
            limit=limit,
            order_id=order_id,
            status=status
        )
        
        receipt_list = [
            {
                "id": receipt.id,
                "order_id": receipt.order_id,
                "receipt_date": receipt.receipt_date.isoformat() if receipt.receipt_date else None,
                "status": receipt.status,
                "created_at": receipt.created_at.isoformat() if receipt.created_at else None
            }
            for receipt in receipts
        ]
        
        return Response.success(data=receipt_list, message="收货记录列表获取成功")
    except Exception as e:
        logger.error(f"获取收货记录失败: {str(e)}")
        return Response.error(message=f"获取收货记录失败: {str(e)}")


@router.post("/goods-receipts/", response_model=Response[dict])
def create_goods_receipt(
    receipt_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建收货记录
    """
    try:
        service = PurchaseService(db)
        receipt = service.create_goods_receipt(receipt_data)
        
        result_data = {
            "id": receipt.id,
            "order_id": receipt.order_id,
            "status": receipt.status
        }
        
        return Response.success(data=result_data, message="收货记录创建成功")
    except Exception as e:
        logger.error(f"创建收货记录失败: {str(e)}")
        return Response.error(message=f"创建收货记录失败: {str(e)}")


@router.get("/requests", response_model=Response[List[dict]])
def get_purchase_requests(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取采购申请列表
    """
    try:
        service = PurchaseService(db)
        requests = service.get_purchase_requests(
            skip=skip,
            limit=limit,
            project_id=project_id,
            status=status
        )
        
        request_list = [
            {
                "id": request.id,
                "request_code": request.request_code,
                "project_id": request.project_id,
                "title": request.title,
                "total_amount": float(request.total_amount or 0),
                "status": request.status,
                "created_at": request.created_at.isoformat() if request.created_at else None
            }
            for request in requests
        ]
        
        return Response.success(data=request_list, message="采购申请列表获取成功")
    except Exception as e:
        logger.error(f"获取采购申请失败: {str(e)}")
        return Response.error(message=f"获取采购申请失败: {str(e)}")


@router.post("/requests", response_model=Response[dict])
def create_purchase_request(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建采购申请
    """
    try:
        service = PurchaseService(db)
        request = service.create_purchase_request(request_data)
        
        result_data = {
            "id": request.id,
            "request_code": request.request_code,
            "status": request.status
        }
        
        return Response.success(data=result_data, message="采购申请创建成功")
    except Exception as e:
        logger.error(f"创建采购申请失败: {str(e)}")
        return Response.error(message=f"创建采购申请失败: {str(e)}")


@router.post("/requests/{request_id}/generate-orders", response_model=Response[str])
def generate_orders_from_request(
    request_id: int,
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    从采购申请生成订单
    """
    try:
        service = PurchaseService(db)
        success = service.generate_orders_from_request(request_id, supplier_id)
        
        if success:
            return Response.success(message="从采购申请生成订单成功")
        else:
            return Response.error(message="采购申请不存在", code=404)
    except Exception as e:
        logger.error(f"从采购申请生成订单失败: {str(e)}")
        return Response.error(message=f"从采购申请生成订单失败: {str(e)}")