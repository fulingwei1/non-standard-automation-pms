# -*- coding: utf-8 -*-
"""仓储管理 - 盘点管理"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.warehouse import StockCountOrder, StockCountItem

router = APIRouter()

class CountItemCreate(BaseModel):
    material_code: str; material_name: Optional[str] = None
    location_id: Optional[int] = None; system_quantity: float = 0

class CountItemOut(BaseModel):
    id: int; material_code: str; material_name: Optional[str] = None
    location_id: Optional[int] = None; system_quantity: float = 0
    actual_quantity: Optional[float] = None; diff_quantity: Optional[float] = None
    diff_reason: Optional[str] = None
    class Config: from_attributes = True

class CountOrderCreate(BaseModel):
    warehouse_id: Optional[int] = None; count_type: str = "FULL"
    planned_date: Optional[date] = None; remark: Optional[str] = None
    items: List[CountItemCreate] = []

class CountOrderOut(BaseModel):
    id: int; count_no: str; warehouse_id: Optional[int] = None
    count_type: str; status: str; planned_date: Optional[date] = None
    actual_date: Optional[date] = None; operator: Optional[str] = None
    remark: Optional[str] = None; total_items: int = 0
    matched_items: int = 0; diff_items: int = 0
    created_at: Optional[str] = None; items: List[CountItemOut] = []
    class Config: from_attributes = True

class CountItemUpdate(BaseModel):
    actual_quantity: float; diff_reason: Optional[str] = None

def _gen_count_no(db):
    today = date.today().strftime("%Y%m%d")
    last = db.query(StockCountOrder).filter(StockCountOrder.count_no.like(f"SC{today}%")).order_by(desc(StockCountOrder.count_no)).first()
    seq = int(last.count_no[-4:])+1 if last else 1
    return f"SC{today}{seq:04d}"

@router.get("/stock-count")
def list_count_orders(status:Optional[str]=Query(None),page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),db:Session=Depends(get_db)):
    q = db.query(StockCountOrder)
    if status: q = q.filter(StockCountOrder.status==status)
    total = q.count()
    items = q.order_by(desc(StockCountOrder.created_at)).offset((page-1)*page_size).limit(page_size).all()
    return {"items":[CountOrderOut.model_validate(i).model_dump() for i in items],"total":total,"page":page,"page_size":page_size}

@router.get("/stock-count/{order_id}",response_model=CountOrderOut)
def get_count_order(order_id:int,db:Session=Depends(get_db)):
    o = db.query(StockCountOrder).filter(StockCountOrder.id==order_id).first()
    if not o: raise HTTPException(404,"盘点单不存在")
    return o

@router.post("/stock-count",response_model=CountOrderOut)
def create_count_order(data:CountOrderCreate,db:Session=Depends(get_db)):
    no = _gen_count_no(db)
    o = StockCountOrder(count_no=no,warehouse_id=data.warehouse_id,count_type=data.count_type,planned_date=data.planned_date,remark=data.remark,total_items=len(data.items),status="DRAFT")
    db.add(o); db.flush()
    for d in data.items: db.add(StockCountItem(order_id=o.id,**d.model_dump()))
    db.commit(); db.refresh(o); return o

@router.put("/stock-count/{order_id}/items/{item_id}",response_model=CountItemOut)
def update_count_item(order_id:int,item_id:int,data:CountItemUpdate,db:Session=Depends(get_db)):
    item = db.query(StockCountItem).filter(StockCountItem.id==item_id,StockCountItem.order_id==order_id).first()
    if not item: raise HTTPException(404,"盘点明细不存在")
    item.actual_quantity = data.actual_quantity
    item.diff_quantity = data.actual_quantity - float(item.system_quantity)
    item.diff_reason = data.diff_reason
    db.commit(); db.refresh(item); return item

@router.put("/stock-count/{order_id}/status")
def update_count_status(order_id:int,status:str=Query(...),db:Session=Depends(get_db)):
    o = db.query(StockCountOrder).filter(StockCountOrder.id==order_id).first()
    if not o: raise HTTPException(404,"盘点单不存在")
    o.status = status
    if status == "COMPLETED":
        o.actual_date = date.today()
        matched = diff = 0
        for item in o.items:
            if item.actual_quantity is not None:
                if item.diff_quantity == 0: matched += 1
                else: diff += 1
        o.matched_items = matched; o.diff_items = diff
    db.commit(); return {"message":"状态更新成功","status":status}
