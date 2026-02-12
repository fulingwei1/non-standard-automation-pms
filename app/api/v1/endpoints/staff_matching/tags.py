# -*- coding: utf-8 -*-
"""
标签管理 API端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.staff_matching import HrTagDict
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/", response_model=List[schemas.TagDictResponse])
def list_tags(
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取标签列表"""
    query = db.query(HrTagDict)

    if tag_type:
        query = query.filter(HrTagDict.tag_type == tag_type)
    if is_active is not None:
        query = query.filter(HrTagDict.is_active == is_active)
    query = apply_keyword_filter(query, HrTagDict, keyword, ["tag_code", "tag_name"])

    tags = query.order_by(HrTagDict.tag_type, apply_pagination(HrTagDict.sort_order), pagination.offset, pagination.limit).all()
    return tags


@router.get("/tree", response_model=List[schemas.TagDictTreeNode])
def get_tag_tree(
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取标签层级树"""
    query = db.query(HrTagDict).filter(HrTagDict.is_active == True)

    if tag_type:
        query = query.filter(HrTagDict.tag_type == tag_type)

    all_tags = query.order_by(HrTagDict.sort_order).all()

    # 构建树结构
    tag_dict = {tag.id: {
        'id': tag.id,
        'tag_code': tag.tag_code,
        'tag_name': tag.tag_name,
        'tag_type': tag.tag_type,
        'weight': tag.weight,
        'is_required': tag.is_required,
        'sort_order': tag.sort_order,
        'children': []
    } for tag in all_tags}

    roots = []
    for tag in all_tags:
        if tag.parent_id and tag.parent_id in tag_dict:
            tag_dict[tag.parent_id]['children'].append(tag_dict[tag.id])
        else:
            roots.append(tag_dict[tag.id])

    return roots


@router.post("/", response_model=schemas.TagDictResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: schemas.TagDictCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建标签"""
    # 检查编码唯一性
    existing = db.query(HrTagDict).filter(HrTagDict.tag_code == tag_data.tag_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"标签编码已存在: {tag_data.tag_code}")

    tag = HrTagDict(**tag_data.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=schemas.TagDictResponse)
def update_tag(
    tag_id: int,
    tag_data: schemas.TagDictUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:update"))
):
    """更新标签"""
    tag = db.query(HrTagDict).filter(HrTagDict.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    for field, value in tag_data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """删除标签（软删除）"""
    tag = db.query(HrTagDict).filter(HrTagDict.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    tag.is_active = False
    db.commit()
    return {"message": "标签已删除"}
