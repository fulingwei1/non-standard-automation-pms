# -*- coding: utf-8 -*-
"""
库存管理API路由
Team 2: 物料全流程跟踪系统
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.inventory_management_service import (
    InventoryManagementService,
    InsufficientStockError
)
from app.services.stock_count_service import StockCountService


router = APIRouter(prefix="/inventory", tags=["inventory"])


# ============ Pydantic Schemas ============

class MaterialStockResponse(BaseModel):
    """库存响应"""
    id: int
    material_id: int
    material_code: str
    material_name: str
    location: str
    batch_number: Optional[str]
    quantity: float
    available_quantity: float
    reserved_quantity: float
    unit: str
    unit_price: float
    total_value: float
    status: str
    last_update: Optional[datetime]

    class Config:
        from_attributes = True


class MaterialTransactionResponse(BaseModel):
    """交易记录响应"""
    id: int
    material_code: str
    material_name: str
    transaction_type: str
    quantity: float
    unit: str
    unit_price: float
    total_amount: float
    source_location: Optional[str]
    target_location: Optional[str]
    batch_number: Optional[str]
    transaction_date: datetime
    remark: Optional[str]

    class Config:
        from_attributes = True


class ReserveMaterialRequest(BaseModel):
    """预留物料请求"""
    material_id: int = Field(..., description="物料ID")
    quantity: float = Field(..., gt=0, description="预留数量")
    project_id: Optional[int] = Field(None, description="项目ID")
    work_order_id: Optional[int] = Field(None, description="工单ID")
    expected_use_date: Optional[date] = Field(None, description="预计使用日期")
    remark: Optional[str] = Field(None, description="备注")


class IssueMaterialRequest(BaseModel):
    """领料请求"""
    material_id: int = Field(..., description="物料ID")
    quantity: float = Field(..., gt=0, description="领料数量")
    location: str = Field(..., description="仓库位置")
    work_order_id: Optional[int] = Field(None, description="工单ID")
    work_order_no: Optional[str] = Field(None, description="工单编号")
    project_id: Optional[int] = Field(None, description="项目ID")
    reservation_id: Optional[int] = Field(None, description="预留单ID")
    cost_method: str = Field("FIFO", description="成本核算方法: FIFO/LIFO/WEIGHTED_AVG")
    remark: Optional[str] = Field(None, description="备注")


class ReturnMaterialRequest(BaseModel):
    """退料请求"""
    material_id: int = Field(..., description="物料ID")
    quantity: float = Field(..., gt=0, description="退料数量")
    location: str = Field(..., description="仓库位置")
    batch_number: Optional[str] = Field(None, description="批次号")
    work_order_id: Optional[int] = Field(None, description="工单ID")
    remark: Optional[str] = Field(None, description="备注")


class TransferStockRequest(BaseModel):
    """库存转移请求"""
    material_id: int = Field(..., description="物料ID")
    quantity: float = Field(..., gt=0, description="转移数量")
    from_location: str = Field(..., description="源位置")
    to_location: str = Field(..., description="目标位置")
    batch_number: Optional[str] = Field(None, description="批次号")
    remark: Optional[str] = Field(None, description="备注")


class CreateCountTaskRequest(BaseModel):
    """创建盘点任务请求"""
    count_type: str = Field("FULL", description="盘点类型: FULL/PARTIAL/CYCLE")
    count_date: date = Field(..., description="盘点日期")
    location: Optional[str] = Field(None, description="盘点位置")
    category_id: Optional[int] = Field(None, description="物料分类ID")
    material_ids: Optional[List[int]] = Field(None, description="物料ID列表(抽盘时使用)")
    assigned_to: Optional[int] = Field(None, description="指派盘点人ID")
    remark: Optional[str] = Field(None, description="备注")


class RecordActualQuantityRequest(BaseModel):
    """录入实盘数量请求"""
    actual_quantity: float = Field(..., description="实盘数量")
    remark: Optional[str] = Field(None, description="备注")


class StockCountDetailResponse(BaseModel):
    """盘点明细响应"""
    id: int
    material_code: str
    material_name: str
    location: Optional[str]
    batch_number: Optional[str]
    system_quantity: float
    actual_quantity: Optional[float]
    difference: Optional[float]
    difference_rate: Optional[float]
    status: str

    class Config:
        from_attributes = True


class StockCountTaskResponse(BaseModel):
    """盘点任务响应"""
    id: int
    task_no: str
    count_type: str
    location: Optional[str]
    count_date: date
    status: str
    total_items: int
    counted_items: int
    matched_items: int
    diff_items: int
    total_diff_value: float

    class Config:
        from_attributes = True


# ============ API Endpoints ============

@router.get("/stocks", response_model=List[MaterialStockResponse])
def get_stocks(
    material_id: Optional[int] = Query(None, description="物料ID"),
    location: Optional[str] = Query(None, description="仓库位置"),
    status: Optional[str] = Query(None, description="库存状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询库存
    
    - **material_id**: 物料ID (可选)
    - **location**: 仓库位置 (可选)
    - **status**: 库存状态 (可选)
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    if material_id:
        stocks = service.get_stock(material_id, location)
    else:
        # 查询所有库存
        from app.models.inventory_tracking import MaterialStock
        query = db.query(MaterialStock).filter(
            MaterialStock.tenant_id == current_user.tenant_id
        )
        if location:
            query = query.filter(MaterialStock.location == location)
        if status:
            query = query.filter(MaterialStock.status == status)
        stocks = query.limit(100).all()
    
    return stocks


@router.get("/stocks/{material_id}/transactions", response_model=List[MaterialTransactionResponse])
def get_material_transactions(
    material_id: int,
    transaction_type: Optional[str] = Query(None, description="交易类型"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, le=500, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询物料交易记录
    
    - **material_id**: 物料ID
    - **transaction_type**: 交易类型 (可选)
    - **start_date**: 开始日期 (可选)
    - **end_date**: 结束日期 (可选)
    - **limit**: 返回数量限制
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    transactions = service.get_transactions(
        material_id=material_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return transactions


@router.post("/reserve")
def reserve_material(
    request: ReserveMaterialRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预留物料
    
    - **material_id**: 物料ID
    - **quantity**: 预留数量
    - **project_id**: 项目ID (可选)
    - **work_order_id**: 工单ID (可选)
    - **expected_use_date**: 预计使用日期 (可选)
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    try:
        reservation = service.reserve_material(
            material_id=request.material_id,
            quantity=Decimal(str(request.quantity)),
            project_id=request.project_id,
            work_order_id=request.work_order_id,
            expected_use_date=request.expected_use_date,
            created_by=current_user.id,
            remark=request.remark
        )
        
        return {
            "success": True,
            "message": "物料预留成功",
            "reservation_id": reservation.id,
            "reservation_no": reservation.reservation_no,
            "reserved_quantity": float(reservation.reserved_quantity)
        }
    
    except InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"预留失败: {str(e)}")


@router.post("/issue")
def issue_material(
    request: IssueMaterialRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    领料出库
    
    - **material_id**: 物料ID
    - **quantity**: 领料数量
    - **location**: 仓库位置
    - **work_order_id**: 工单ID (可选)
    - **project_id**: 项目ID (可选)
    - **reservation_id**: 预留单ID (可选)
    - **cost_method**: 成本核算方法 (FIFO/LIFO/WEIGHTED_AVG)
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    try:
        result = service.issue_material(
            material_id=request.material_id,
            quantity=Decimal(str(request.quantity)),
            location=request.location,
            work_order_id=request.work_order_id,
            work_order_no=request.work_order_no,
            project_id=request.project_id,
            operator_id=current_user.id,
            reservation_id=request.reservation_id,
            remark=request.remark,
            cost_method=request.cost_method
        )
        
        return {
            "success": True,
            "message": result['message'],
            "total_quantity": float(result['total_quantity']),
            "total_cost": float(result['total_cost']),
            "transactions": len(result['transactions'])
        }
    
    except InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"领料失败: {str(e)}")


@router.post("/return")
def return_material(
    request: ReturnMaterialRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    退料入库
    
    - **material_id**: 物料ID
    - **quantity**: 退料数量
    - **location**: 仓库位置
    - **batch_number**: 批次号 (可选)
    - **work_order_id**: 工单ID (可选)
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    try:
        result = service.return_material(
            material_id=request.material_id,
            quantity=Decimal(str(request.quantity)),
            location=request.location,
            batch_number=request.batch_number,
            work_order_id=request.work_order_id,
            operator_id=current_user.id,
            remark=request.remark
        )
        
        return {
            "success": True,
            "message": result['message'],
            "transaction_id": result['transaction'].id,
            "stock_quantity": float(result['stock'].quantity)
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"退料失败: {str(e)}")


@router.post("/transfer")
def transfer_stock(
    request: TransferStockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    库存转移
    
    - **material_id**: 物料ID
    - **quantity**: 转移数量
    - **from_location**: 源位置
    - **to_location**: 目标位置
    - **batch_number**: 批次号 (可选)
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    try:
        result = service.transfer_stock(
            material_id=request.material_id,
            quantity=Decimal(str(request.quantity)),
            from_location=request.from_location,
            to_location=request.to_location,
            batch_number=request.batch_number,
            operator_id=current_user.id,
            remark=request.remark
        )
        
        return {
            "success": True,
            "message": result['message'],
            "from_stock_quantity": float(result['from_stock'].quantity),
            "to_stock_quantity": float(result['to_stock'].quantity)
        }
    
    except InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"转移失败: {str(e)}")


@router.get("/count/tasks", response_model=List[StockCountTaskResponse])
def get_count_tasks(
    status: Optional[str] = Query(None, description="任务状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(50, le=200, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询盘点任务列表
    
    - **status**: 任务状态 (可选)
    - **start_date**: 开始日期 (可选)
    - **end_date**: 结束日期 (可选)
    """
    service = StockCountService(db, current_user.tenant_id)
    
    tasks = service.get_count_tasks(
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return tasks


@router.post("/count/tasks", response_model=StockCountTaskResponse)
def create_count_task(
    request: CreateCountTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建盘点任务
    
    - **count_type**: 盘点类型 (FULL-全盘, PARTIAL-抽盘, CYCLE-循环盘点)
    - **count_date**: 盘点日期
    - **location**: 盘点位置 (可选)
    - **category_id**: 物料分类ID (可选)
    - **material_ids**: 物料ID列表 (抽盘时使用)
    - **assigned_to**: 指派盘点人ID (可选)
    """
    service = StockCountService(db, current_user.tenant_id)
    
    try:
        task = service.create_count_task(
            count_type=request.count_type,
            count_date=request.count_date,
            location=request.location,
            category_id=request.category_id,
            material_ids=request.material_ids,
            created_by=current_user.id,
            assigned_to=request.assigned_to,
            remark=request.remark
        )
        
        return task
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建盘点任务失败: {str(e)}")


@router.get("/count/tasks/{task_id}/details", response_model=List[StockCountDetailResponse])
def get_count_details(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取盘点明细列表"""
    service = StockCountService(db, current_user.tenant_id)
    
    details = service.get_count_details(task_id)
    return details


@router.put("/count/details/{detail_id}")
def record_actual_quantity(
    detail_id: int,
    request: RecordActualQuantityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    录入实盘数量
    
    - **detail_id**: 盘点明细ID
    - **actual_quantity**: 实盘数量
    """
    service = StockCountService(db, current_user.tenant_id)
    
    try:
        detail = service.record_actual_quantity(
            detail_id=detail_id,
            actual_quantity=Decimal(str(request.actual_quantity)),
            counted_by=current_user.id,
            remark=request.remark
        )
        
        return {
            "success": True,
            "message": "录入成功",
            "detail_id": detail.id,
            "system_quantity": float(detail.system_quantity),
            "actual_quantity": float(detail.actual_quantity or 0),
            "difference": float(detail.difference or 0),
            "difference_rate": float(detail.difference_rate or 0)
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"录入失败: {str(e)}")


@router.post("/count/tasks/{task_id}/approve")
def approve_count_task(
    task_id: int,
    auto_adjust: bool = Query(True, description="是否自动执行库存调整"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批准盘点调整
    
    - **task_id**: 盘点任务ID
    - **auto_adjust**: 是否自动执行库存调整
    """
    service = StockCountService(db, current_user.tenant_id)
    
    try:
        result = service.approve_adjustment(
            task_id=task_id,
            approved_by=current_user.id,
            auto_adjust=auto_adjust
        )
        
        return {
            "success": True,
            "message": result['message'],
            "total_adjustments": result['total_adjustments'],
            "total_diff_value": result['total_diff_value']
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审批失败: {str(e)}")


@router.get("/analysis/turnover")
def get_turnover_analysis(
    material_id: Optional[int] = Query(None, description="物料ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    库存周转率分析
    
    - **material_id**: 物料ID (可选,不填则分析所有物料)
    - **start_date**: 开始日期 (可选)
    - **end_date**: 结束日期 (可选)
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    result = service.calculate_turnover_rate(
        material_id=material_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return result


@router.get("/analysis/aging")
def get_aging_analysis(
    location: Optional[str] = Query(None, description="仓库位置"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    库龄分析
    
    - **location**: 仓库位置 (可选)
    
    返回物料库龄分析,按0-30天、31-90天、91-180天、181-365天、365天以上分类
    """
    service = InventoryManagementService(db, current_user.tenant_id)
    
    result = service.analyze_aging(location=location)
    
    # 按库龄分组统计
    aging_summary = {}
    for item in result:
        category = item['aging_category']
        if category not in aging_summary:
            aging_summary[category] = {
                'count': 0,
                'total_quantity': 0,
                'total_value': 0
            }
        
        aging_summary[category]['count'] += 1
        aging_summary[category]['total_quantity'] += item['quantity']
        aging_summary[category]['total_value'] += item['total_value']
    
    return {
        "aging_summary": aging_summary,
        "details": result
    }
