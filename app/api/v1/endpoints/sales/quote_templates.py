# -*- coding: utf-8 -*-
"""
报价模板管理
包含：模板CRUD、版本管理、从模板创建报价
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.core import security
from app.models.sales import QuoteTemplate, QuoteTemplateVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination

router = APIRouter()


@router.get("/quotes/templates", response_model=ResponseModel)
def get_quote_templates(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
    visibility_scope: Optional[str] = Query(None, description="可见范围"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价模板列表

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        status: 状态筛选
        visibility_scope: 可见范围筛选
        current_user: 当前用户

    Returns:
        ResponseModel: 模板列表
    """
    query = db.query(QuoteTemplate).options(
        joinedload(QuoteTemplate.versions)
    )

    if status:
        query = query.filter(QuoteTemplate.status == status)
    if visibility_scope:
        query = query.filter(QuoteTemplate.visibility_scope == visibility_scope)

    # 按可见范围过滤
    query = query.filter(
        (QuoteTemplate.visibility_scope == "PUBLIC") |
        (QuoteTemplate.created_by == current_user.id)
    )

    total = query.count()
    templates = apply_pagination(query.order_by(desc(QuoteTemplate.created_at)), pagination.offset, pagination.limit).all()

    templates_data = [{
        "id": t.id,
        "template_code": t.template_code,
        "template_name": t.template_name,
        "description": t.description,
        "status": t.status,
        "visibility_scope": t.visibility_scope,
        "current_version_id": t.current_version_id,
        "version_count": len(t.versions) if t.versions else 0,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in templates]

    return ResponseModel(
        code=200,
        message="获取模板列表成功",
        data={"total": total, "items": templates_data}
    )


@router.get("/quotes/templates/{template_id}", response_model=ResponseModel)
def get_template_detail(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取模板详情

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 模板详情
    """
    template = db.query(QuoteTemplate).options(
        joinedload(QuoteTemplate.versions)
    ).filter(QuoteTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 权限检查
    if template.visibility_scope != "PUBLIC" and template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此模板")

    versions_data = [{
        "id": v.id,
        "version_no": v.version_no,
        "status": v.status,
        "content_json": v.content_json,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    } for v in template.versions] if template.versions else []

    return ResponseModel(
        code=200,
        message="获取模板详情成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "description": template.description,
            "status": template.status,
            "visibility_scope": template.visibility_scope,
            "current_version_id": template.current_version_id,
            "versions": versions_data,
            "created_at": template.created_at.isoformat() if template.created_at else None,
        }
    )


@router.post("/quotes/templates", response_model=ResponseModel)
def create_quote_template(
    template_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建报价模板

    Args:
        template_data: 模板数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    # 生成模板编码
    count = db.query(QuoteTemplate).count()
    template_code = f"QT{datetime.now().strftime('%y%m%d')}{count + 1:03d}"

    template = QuoteTemplate(
        template_code=template_code,
        template_name=template_data.get("template_name", "新模板"),
        description=template_data.get("description"),
        status="DRAFT",
        visibility_scope=template_data.get("visibility_scope", "PRIVATE"),
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()

    # 创建初始版本
    version = QuoteTemplateVersion(
        template_id=template.id,
        version_no=1,
        status="DRAFT",
        content_json=template_data.get("content_json", "{}"),
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()

    template.current_version_id = version.id
    db.commit()

    return ResponseModel(
        code=200,
        message="模板创建成功",
        data={"id": template.id, "template_code": template_code}
    )


@router.put("/quotes/templates/{template_id}", response_model=ResponseModel)
def update_quote_template(
    template_id: int,
    template_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新报价模板

    Args:
        template_id: 模板ID
        template_data: 模板数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    template = db.query(QuoteTemplate).filter(QuoteTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限修改此模板")

    updatable = ["template_name", "description", "visibility_scope", "status"]
    for field in updatable:
        if field in template_data:
            setattr(template, field, template_data[field])

    db.commit()

    return ResponseModel(code=200, message="模板更新成功", data={"id": template.id})


@router.delete("/quotes/templates/{template_id}", response_model=ResponseModel)
def delete_quote_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除报价模板

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    template = db.query(QuoteTemplate).filter(QuoteTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限删除此模板")

    if template.status == "PUBLISHED":
        raise HTTPException(status_code=400, detail="已发布的模板不能删除")

    db.delete(template)
    db.commit()

    return ResponseModel(code=200, message="模板删除成功", data={"id": template_id})


@router.post("/quotes/templates/{template_id}/versions", response_model=ResponseModel)
def create_template_version(
    template_id: int,
    version_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建模板新版本

    Args:
        template_id: 模板ID
        version_data: 版本数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    template = db.query(QuoteTemplate).filter(QuoteTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限操作此模板")

    # 获取最大版本号
    max_version = db.query(QuoteTemplateVersion).filter(
        QuoteTemplateVersion.template_id == template_id
    ).order_by(desc(QuoteTemplateVersion.version_no)).first()

    new_version_no = (max_version.version_no + 1) if max_version else 1

    version = QuoteTemplateVersion(
        template_id=template_id,
        version_no=new_version_no,
        status="DRAFT",
        content_json=version_data.get("content_json", "{}"),
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    return ResponseModel(
        code=200,
        message="版本创建成功",
        data={"id": version.id, "version_no": new_version_no}
    )


@router.post("/quotes/templates/{template_id}/publish", response_model=ResponseModel)
def publish_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    发布模板

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 发布结果
    """
    template = db.query(QuoteTemplate).filter(QuoteTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限操作此模板")

    if not template.current_version_id:
        raise HTTPException(status_code=400, detail="模板没有版本，无法发布")

    # 更新当前版本状态
    version = db.query(QuoteTemplateVersion).filter(
        QuoteTemplateVersion.id == template.current_version_id
    ).first()
    if version:
        version.status = "PUBLISHED"
        version.published_at = datetime.now()
        version.published_by = current_user.id

    template.status = "PUBLISHED"
    db.commit()

    return ResponseModel(code=200, message="模板发布成功", data={"id": template.id})
