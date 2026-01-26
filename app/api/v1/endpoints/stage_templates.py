# -*- coding: utf-8 -*-
"""
阶段模板管理 API
提供模板的 CRUD、复制、导入导出等接口
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.stage_template import (
    NodeDefinitionCreate,
    NodeDefinitionResponse,
    NodeDefinitionUpdate,
    ReorderNodesRequest,
    ReorderStagesRequest,
    SetNodeDependenciesRequest,
    StageDefinitionCreate,
    StageDefinitionResponse,
    StageDefinitionUpdate,
    StageTemplateCopy,
    StageTemplateCreate,
    StageTemplateDetail,
    StageTemplateResponse,
    StageTemplateUpdate,
    TemplateExportData,
    TemplateImportRequest,
)
from app.services.stage_template import StageTemplateService

router = APIRouter()


# ==================== 模板管理 ====================


@router.get("/", response_model=List[StageTemplateResponse])
def list_templates(
    db: Session = Depends(deps.get_db),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    is_active: Optional[bool] = Query(True, description="是否启用"),
    include_stages: bool = Query(False, description="是否包含阶段信息"),
) -> Any:
    """获取模板列表"""
    service = StageTemplateService(db)
    return service.list_templates(
        project_type=project_type,
        is_active=is_active,
        include_stages=include_stages,
    )


@router.get("/{template_id}", response_model=StageTemplateDetail)
def get_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """获取模板详情（包含阶段和节点）"""
    service = StageTemplateService(db)
    template = service.get_template(template_id, include_stages=True, include_nodes=True)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/", response_model=StageTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_in: StageTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """创建模板"""
    service = StageTemplateService(db)
    try:
        template = service.create_template(
            template_code=template_in.template_code,
            template_name=template_in.template_name,
            description=template_in.description,
            project_type=template_in.project_type,
            is_default=template_in.is_default,
            created_by=current_user.id,
        )
        db.commit()
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{template_id}", response_model=StageTemplateResponse)
def update_template(
    template_id: int,
    template_in: StageTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """更新模板"""
    service = StageTemplateService(db)
    template = service.update_template(
        template_id,
        **template_in.model_dump(exclude_unset=True)
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.commit()
    return template


@router.delete("/{template_id}", response_model=MessageResponse)
def delete_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """删除模板"""
    service = StageTemplateService(db)
    try:
        success = service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="模���不存在")
        db.commit()
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{template_id}/copy", response_model=StageTemplateResponse)
def copy_template(
    template_id: int,
    copy_in: StageTemplateCopy,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """复制模板"""
    service = StageTemplateService(db)
    try:
        new_template = service.copy_template(
            source_template_id=template_id,
            new_code=copy_in.new_code,
            new_name=copy_in.new_name,
            created_by=current_user.id,
        )
        db.commit()
        return new_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{template_id}/set-default", response_model=StageTemplateResponse)
def set_default_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """设置为默认模板"""
    service = StageTemplateService(db)
    try:
        template = service.set_default_template(template_id)
        db.commit()
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/default/{project_type}", response_model=StageTemplateResponse)
def get_default_template(
    project_type: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """获取指定项目类型的默认模板"""
    service = StageTemplateService(db)
    template = service.get_default_template(project_type)
    if not template:
        raise HTTPException(status_code=404, detail=f"未找到项目类型 {project_type} 的默认模板")
    return template


# ==================== 阶段定义管理 ====================


@router.post("/{template_id}/stages", response_model=StageDefinitionResponse, status_code=status.HTTP_201_CREATED)
def add_stage(
    template_id: int,
    stage_in: StageDefinitionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """添加阶段定义"""
    if stage_in.template_id != template_id:
        raise HTTPException(status_code=400, detail="模板ID不匹配")

    service = StageTemplateService(db)
    try:
        stage = service.add_stage(
            template_id=template_id,
            stage_code=stage_in.stage_code,
            stage_name=stage_in.stage_name,
            sequence=stage_in.sequence,
            estimated_days=stage_in.estimated_days,
            description=stage_in.description,
            is_required=stage_in.is_required,
        )
        db.commit()
        return stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/stages/{stage_id}", response_model=StageDefinitionResponse)
def update_stage(
    stage_id: int,
    stage_in: StageDefinitionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """更新阶段定义"""
    service = StageTemplateService(db)
    stage = service.update_stage(stage_id, **stage_in.model_dump(exclude_unset=True))
    if not stage:
        raise HTTPException(status_code=404, detail="阶段不存在")
    db.commit()
    return stage


@router.delete("/stages/{stage_id}", response_model=MessageResponse)
def delete_stage(
    stage_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """删除阶段定义"""
    service = StageTemplateService(db)
    success = service.delete_stage(stage_id)
    if not success:
        raise HTTPException(status_code=404, detail="阶段不存在")
    db.commit()
    return {"message": "删除成功"}


@router.post("/{template_id}/stages/reorder", response_model=MessageResponse)
def reorder_stages(
    template_id: int,
    reorder_in: ReorderStagesRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """重新排序阶段"""
    service = StageTemplateService(db)
    service.reorder_stages(template_id, reorder_in.stage_ids)
    db.commit()
    return {"message": "排序成功"}


# ==================== 节点定义管理 ====================


@router.post("/stages/{stage_id}/nodes", response_model=NodeDefinitionResponse, status_code=status.HTTP_201_CREATED)
def add_node(
    stage_id: int,
    node_in: NodeDefinitionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """添加节点定义"""
    if node_in.stage_definition_id != stage_id:
        raise HTTPException(status_code=400, detail="阶段ID不匹配")

    service = StageTemplateService(db)
    try:
        node = service.add_node(
            stage_definition_id=stage_id,
            node_code=node_in.node_code,
            node_name=node_in.node_name,
            node_type=node_in.node_type,
            sequence=node_in.sequence,
            estimated_days=node_in.estimated_days,
            completion_method=node_in.completion_method,
            dependency_node_ids=node_in.dependency_node_ids,
            is_required=node_in.is_required,
            required_attachments=node_in.required_attachments,
            approval_role_ids=node_in.approval_role_ids,
            auto_condition=node_in.auto_condition,
            description=node_in.description,
        )
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/nodes/{node_id}", response_model=NodeDefinitionResponse)
def update_node(
    node_id: int,
    node_in: NodeDefinitionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """更新节点定义"""
    service = StageTemplateService(db)
    node = service.update_node(node_id, **node_in.model_dump(exclude_unset=True))
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    db.commit()
    return node


@router.delete("/nodes/{node_id}", response_model=MessageResponse)
def delete_node(
    node_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """删除节点定义"""
    service = StageTemplateService(db)
    success = service.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="节点不存在")
    db.commit()
    return {"message": "删除成功"}


@router.post("/stages/{stage_id}/nodes/reorder", response_model=MessageResponse)
def reorder_nodes(
    stage_id: int,
    reorder_in: ReorderNodesRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """重新排序节点"""
    service = StageTemplateService(db)
    service.reorder_nodes(stage_id, reorder_in.node_ids)
    db.commit()
    return {"message": "排序成功"}


@router.put("/nodes/{node_id}/dependencies", response_model=NodeDefinitionResponse)
def set_node_dependencies(
    node_id: int,
    deps_in: SetNodeDependenciesRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """设置节点依赖关系"""
    service = StageTemplateService(db)
    try:
        node = service.set_node_dependencies(node_id, deps_in.dependency_node_ids)
        db.commit()
        return node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 导入导出 ====================


@router.get("/{template_id}/export", response_model=TemplateExportData)
def export_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """导出模板为JSON"""
    service = StageTemplateService(db)
    try:
        return service.export_template(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/import", response_model=StageTemplateResponse, status_code=status.HTTP_201_CREATED)
def import_template(
    import_in: TemplateImportRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """从JSON导入模板"""
    service = StageTemplateService(db)
    try:
        template = service.import_template(
            data=import_in.data,
            created_by=current_user.id,
            override_code=import_in.override_code,
            override_name=import_in.override_name,
        )
        db.commit()
        return template
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
