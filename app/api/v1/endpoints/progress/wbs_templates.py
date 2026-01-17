# -*- coding: utf-8 -*-
"""
进度跟踪模块 - WBS模板管理
包含：WBS模板CRUD、模板任务管理、模板复制
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.progress import WbsTemplate, WbsTemplateTask
from app.models.user import User
from app.schemas.progress import (
    WbsTemplateCreate,
    WbsTemplateListResponse,
    WbsTemplateResponse,
    WbsTemplateTaskCreate,
    WbsTemplateTaskResponse,
    WbsTemplateTaskUpdate,
    WbsTemplateUpdate,
)

router = APIRouter()


# ==================== WBS 模板管理 ====================

@router.get("/wbs-templates", response_model=WbsTemplateListResponse, status_code=status.HTTP_200_OK)
def read_wbs_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（模板编码/名称）"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取WBS模板列表（支持分页和筛选）
    """
    query = db.query(WbsTemplate)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                WbsTemplate.template_code.like(f"%{keyword}%"),
                WbsTemplate.template_name.like(f"%{keyword}%"),
            )
        )

    # 项目类型筛选
    if project_type:
        query = query.filter(WbsTemplate.project_type == project_type)

    # 设备类型筛选
    if equipment_type:
        query = query.filter(WbsTemplate.equipment_type == equipment_type)

    # 启用状态筛选
    if is_active is not None:
        query = query.filter(WbsTemplate.is_active == is_active)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    templates = query.order_by(WbsTemplate.created_at.desc()).offset(offset).limit(page_size).all()

    return WbsTemplateListResponse(
        items=templates,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/wbs-templates/{template_id}", response_model=WbsTemplateResponse, status_code=status.HTTP_200_OK)
def read_wbs_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取WBS模板详情
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    return template


@router.post("/wbs-templates", response_model=WbsTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: WbsTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建WBS模板
    """
    # 检查模板编码是否已存在
    existing = db.query(WbsTemplate).filter(WbsTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = WbsTemplate(**template_in.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.put("/wbs-templates/{template_id}", response_model=WbsTemplateResponse, status_code=status.HTTP_200_OK)
def update_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: WbsTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新WBS模板
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.delete("/wbs-templates/{template_id}", status_code=status.HTTP_200_OK)
def delete_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除WBS模板
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    # 检查是否有项目使用此模板（通过检查是否有任务关联此模板）
    # 这里简化处理，实际应该检查项目是否从该模板初始化
    # 暂时允许删除，因为模板任务会通过cascade自动删除

    db.delete(template)
    db.commit()

    return {"message": "WBS模板已删除", "id": template_id}


@router.post("/wbs-templates/{template_id}/copy", response_model=WbsTemplateResponse, status_code=status.HTTP_201_CREATED)
def copy_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    new_template_code: str = Query(..., description="新模板编码"),
    new_template_name: Optional[str] = Query(None, description="新模板名称"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复制WBS模板
    """
    # 获取原模板
    original_template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not original_template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    # 检查新模板编码是否已存在
    existing = db.query(WbsTemplate).filter(WbsTemplate.template_code == new_template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    # 创建新模板
    new_template = WbsTemplate(
        template_code=new_template_code,
        template_name=new_template_name or f"{original_template.template_name} (副本)",
        project_type=original_template.project_type,
        equipment_type=original_template.equipment_type,
        version_no="V1",
        is_active=original_template.is_active
    )
    db.add(new_template)
    db.flush()  # 获取new_template.id

    # 复制模板任务
    original_tasks = db.query(WbsTemplateTask).filter(
        WbsTemplateTask.template_id == template_id
    ).all()

    task_map = {}  # 原任务ID -> 新任务ID
    for original_task in original_tasks:
        new_task = WbsTemplateTask(
            template_id=new_template.id,
            task_name=original_task.task_name,
            stage=original_task.stage,
            default_owner_role=original_task.default_owner_role,
            plan_days=original_task.plan_days,
            weight=original_task.weight,
            depends_on_template_task_id=None  # 稍后更新
        )
        db.add(new_task)
        db.flush()  # 获取new_task.id
        task_map[original_task.id] = new_task.id

    # 更新依赖关系
    for original_task in original_tasks:
        if original_task.depends_on_template_task_id:
            new_task_id = task_map.get(original_task.id)
            new_depends_id = task_map.get(original_task.depends_on_template_task_id)
            if new_task_id and new_depends_id:
                new_task = db.query(WbsTemplateTask).filter(WbsTemplateTask.id == new_task_id).first()
                if new_task:
                    new_task.depends_on_template_task_id = new_depends_id

    db.commit()
    db.refresh(new_template)

    return new_template


# ==================== WBS 模板任务管理 ====================

@router.get("/wbs-templates/{template_id}/tasks", response_model=List[WbsTemplateTaskResponse], status_code=status.HTTP_200_OK)
def read_wbs_template_tasks(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取WBS模板任务列表
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    tasks = db.query(WbsTemplateTask).filter(WbsTemplateTask.template_id == template_id).order_by(WbsTemplateTask.id).all()

    return tasks


@router.post("/wbs-templates/{template_id}/tasks", response_model=WbsTemplateTaskResponse, status_code=status.HTTP_201_CREATED)
def create_wbs_template_task(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    task_in: WbsTemplateTaskCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加WBS模板任务
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    # 验证依赖任务是否存在
    if task_in.depends_on_template_task_id:
        depends_task = db.query(WbsTemplateTask).filter(
            WbsTemplateTask.id == task_in.depends_on_template_task_id,
            WbsTemplateTask.template_id == template_id
        ).first()
        if not depends_task:
            raise HTTPException(status_code=400, detail="依赖的模板任务不存在")

    task = WbsTemplateTask(template_id=template_id, **task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/wbs-template-tasks/{task_id}", response_model=WbsTemplateTaskResponse, status_code=status.HTTP_200_OK)
def update_wbs_template_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    task_in: WbsTemplateTaskUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新WBS模板任务
    """
    task = db.query(WbsTemplateTask).filter(WbsTemplateTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="模板任务不存在")

    update_data = task_in.model_dump(exclude_unset=True)

    # 验证依赖任务
    if "depends_on_template_task_id" in update_data and update_data["depends_on_template_task_id"]:
        depends_task = db.query(WbsTemplateTask).filter(
            WbsTemplateTask.id == update_data["depends_on_template_task_id"],
            WbsTemplateTask.template_id == task.template_id
        ).first()
        if not depends_task:
            raise HTTPException(status_code=400, detail="依赖的模板任务不存在")

    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.delete("/wbs-template-tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_wbs_template_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除WBS模板任务
    """
    task = db.query(WbsTemplateTask).filter(WbsTemplateTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="模板任务不存在")

    # 检查是否有其他任务依赖此任务
    dependent_tasks = db.query(WbsTemplateTask).filter(
        WbsTemplateTask.depends_on_template_task_id == task_id
    ).count()

    if dependent_tasks > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除任务，有 {dependent_tasks} 个任务依赖此任务"
        )

    db.delete(task)
    db.commit()

    return {"message": "模板任务已删除", "id": task_id}
