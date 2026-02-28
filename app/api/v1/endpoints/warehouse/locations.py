# -*- coding: utf-8 -*-
"""仓储管理 - 库位管理"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.warehouse import Warehouse, WarehouseLocation

router = APIRouter()

class LocationCreate(BaseModel):
    warehouse_id: int; location_code: str; location_name: Optional[str] = None
    zone: Optional[str] = None; aisle: Optional[str] = None; shelf: Optional[str] = None
    level: Optional[str] = None; position: Optional[str] = None
    capacity: Optional[float] = None; location_type: str = "STORAGE"

class LocationUpdate(BaseModel):
    location_name: Optional[str] = None; zone: Optional[str] = None
    aisle: Optional[str] = None; shelf: Optional[str] = None
    level: Optional[str] = None; position: Optional[str] = None
    capacity: Optional[float] = None; location_type: Optional[str] = None
    is_active: Optional[bool] = None

class LocationOut(BaseModel):
    id: int; warehouse_id: int; location_code: str
    location_name: Optional[str] = None; zone: Optional[str] = None
    aisle: Optional[str] = None; shelf: Optional[str] = None
    level: Optional[str] = None; position: Optional[str] = None
    capacity: Optional[float] = None; location_type: str = "STORAGE"
    is_active: bool = True; warehouse_name: Optional[str] = None
    class Config: from_attributes = True

@router.get("/locations")
def list_locations(warehouse_id:Optional[int]=Query(None),zone:Optional[str]=Query(None),keyword:Optional[str]=Query(None),is_active:Optional[bool]=Query(None),page:int=Query(1,ge=1),page_size:int=Query(50,ge=1,le=10000),db:Session=Depends(get_db)):
    q = db.query(WarehouseLocation)
    if warehouse_id: q = q.filter(WarehouseLocation.warehouse_id==warehouse_id)
    if zone: q = q.filter(WarehouseLocation.zone==zone)
    if is_active is not None: q = q.filter(WarehouseLocation.is_active==is_active)
    if keyword: q = q.filter((WarehouseLocation.location_code.contains(keyword))|(WarehouseLocation.location_name.contains(keyword)))
    total = q.count()
    rows = q.order_by(WarehouseLocation.location_code).offset((page-1)*page_size).limit(page_size).all()
    wh_ids = {r.warehouse_id for r in rows}
    wh_map = {}
    if wh_ids:
        wh_map = {w.id:w.warehouse_name for w in db.query(Warehouse).filter(Warehouse.id.in_(wh_ids)).all()}
    items = []
    for r in rows:
        d = LocationOut.model_validate(r).model_dump()
        d["warehouse_name"] = wh_map.get(r.warehouse_id,"")
        items.append(d)
    return {"items":items,"total":total,"page":page,"page_size":page_size}

@router.post("/locations",response_model=LocationOut)
def create_location(data:LocationCreate,db:Session=Depends(get_db)):
    loc = WarehouseLocation(**data.model_dump()); db.add(loc); db.commit(); db.refresh(loc); return loc

@router.put("/locations/{location_id}",response_model=LocationOut)
def update_location(location_id:int,data:LocationUpdate,db:Session=Depends(get_db)):
    loc = db.query(WarehouseLocation).filter(WarehouseLocation.id==location_id).first()
    if not loc: raise HTTPException(404,"库位不存在")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(loc,k,v)
    db.commit(); db.refresh(loc); return loc

@router.delete("/locations/{location_id}")
def delete_location(location_id:int,db:Session=Depends(get_db)):
    loc = db.query(WarehouseLocation).filter(WarehouseLocation.id==location_id).first()
    if not loc: raise HTTPException(404,"库位不存在")
    loc.is_active = False; db.commit(); return {"message":"库位已禁用"}
