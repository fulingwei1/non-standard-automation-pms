# -*- coding: utf-8 -*-
"""
模板配置 CRUD 操作
"""

import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project_template_config import ProjectTemplateConfig, StageConfig, NodeConfig
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_configs(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    base_template: Optional[str] = Query(None, description="基础模板编码"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取模板配置列表"""
    offset = (page - 1) * page_size
    
    query = db.query(ProjectTemplateConfig).filter(ProjectTemplateConfig.is_active == True)
    
    if base_template:
        query = query.filter(ProjectTemplateConfig.base_template_code == base_template)
    if is_active is not None:
        query = query.filter(ProjectTemplateConfig.is_active == is_active)
    
    total = query.count()
    items = query.offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=[{
            "id": item.id,
            "config_code": item.config_code,
            "config_name": item.config_name,
            "description": item.description,
            "base_template_code": item.base_template_code,
            "is_active": item.is_active,
            "is_default": item.is_default,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        } for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{config_id}", response_model=dict)
def get_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int = Path(..., ge=1),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取模板配置详情（含阶段和节点）"""
    config = db.query(ProjectTemplateConfig).filter(
        ProjectTemplateConfig.id == config_id,
        ProjectTemplateConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 加载阶段和节点
    stages = []
    for stage in sorted(config.stages, key=lambda s: s.sequence):
        nodes = []
        for node in sorted(stage.nodes, key=lambda n: n.sequence):
            nodes.append({
                "id": node.id,
                "node_code": node.node_code,
                "node_name": node.node_name,
                "sequence": node.sequence,
                "is_enabled": node.is_enabled,
                "is_required": node.is_required,
                "custom_owner_role_code": node.custom_owner_role_code,
                "custom_estimated_days": node.custom_estimated_days,
            })
        
        stages.append({
            "id": stage.id,
            "stage_code": stage.stage_code,
            "stage_name": stage.stage_name,
            "sequence": stage.sequence,
            "is_enabled": stage.is_enabled,
            "is_required": stage.is_required,
            "custom_description": stage.custom_description,
            "custom_estimated_days": stage.custom_estimated_days,
            "nodes": nodes,
        })
    
    return {
        "id": config.id,
        "config_code": config.config_code,
        "config_name": config.config_name,
        "description": config.description,
        "base_template_code": config.base_template_code,
        "config_json": json.loads(config.config_json) if config.config_json else {},
        "is_active": config.is_active,
        "is_default": config.is_default,
        "stages": stages,
    }


@router.post("", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_config(
    *,
    db: Session = Depends(deps.get_db),
    config_data: dict,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建模板配置"""
    # 检查编码是否重复
    existing = db.query(ProjectTemplateConfig).filter(
        ProjectTemplateConfig.config_code == config_data.get("config_code")
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置编码已存在")
    
    # 创建配置
    config = ProjectTemplateConfig(
        config_code=config_data.get("config_code"),
        config_name=config_data.get("config_name"),
        description=config_data.get("description", ""),
        base_template_code=config_data.get("base_template_code"),
        config_json=json.dumps(config_data.get("config", {})),
        is_active=config_data.get("is_active", True),
        is_default=False,
        created_by=current_user.id,
    )
    
    db.add(config)
    db.flush()
    
    # 创建阶段和节点配置
    stages_data = config_data.get("stages", [])
    for stage_data in stages_data:
        stage = StageConfig(
            config_id=config.id,
            stage_code=stage_data.get("stage_code"),
            stage_name=stage_data.get("stage_name", ""),
            sequence=stage_data.get("sequence", 0),
            is_enabled=stage_data.get("is_enabled", True),
            is_required=stage_data.get("is_required", False),
            custom_description=stage_data.get("custom_description"),
            custom_estimated_days=stage_data.get("custom_estimated_days"),
        )
        db.add(stage)
        db.flush()
        
        # 创建节点
        nodes_data = stage_data.get("nodes", [])
        for node_data in nodes_data:
            node = NodeConfig(
                stage_config_id=stage.id,
                node_code=node_data.get("node_code"),
                node_name=node_data.get("node_name", ""),
                sequence=node_data.get("sequence", 0),
                is_enabled=node_data.get("is_enabled", True),
                is_required=node_data.get("is_required", False),
                custom_owner_role_code=node_data.get("custom_owner_role_code"),
                custom_estimated_days=node_data.get("custom_estimated_days"),
            )
            db.add(node)
    
    db.commit()
    db.refresh(config)
    
    return ResponseModel(message="创建成功", data={"id": config.id})


@router.put("/{config_id}", response_model=ResponseModel)
def update_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int = Path(..., ge=1),
    config_data: dict,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新模板配置"""
    config = db.query(ProjectTemplateConfig).filter(
        ProjectTemplateConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 更新基本信息
    config.config_name = config_data.get("config_name", config.config_name)
    config.description = config_data.get("description", config.description)
    config.config_json = json.dumps(config_data.get("config", {}))
    config.is_active = config_data.get("is_active", config.is_active)
    
    # 更新阶段和节点（简化：先删除再创建）
    db.query(StageConfig).filter(StageConfig.config_id == config_id).delete()
    
    stages_data = config_data.get("stages", [])
    for stage_data in stages_data:
        stage = StageConfig(
            config_id=config.id,
            stage_code=stage_data.get("stage_code"),
            stage_name=stage_data.get("stage_name", ""),
            sequence=stage_data.get("sequence", 0),
            is_enabled=stage_data.get("is_enabled", True),
            is_required=stage_data.get("is_required", False),
            custom_description=stage_data.get("custom_description"),
            custom_estimated_days=stage_data.get("custom_estimated_days"),
        )
        db.add(stage)
        db.flush()
        
        nodes_data = stage_data.get("nodes", [])
        for node_data in nodes_data:
            node = NodeConfig(
                stage_config_id=stage.id,
                node_code=node_data.get("node_code"),
                node_name=node_data.get("node_name", ""),
                sequence=node_data.get("sequence", 0),
                is_enabled=node_data.get("is_enabled", True),
                is_required=node_data.get("is_required", False),
                custom_owner_role_code=node_data.get("custom_owner_role_code"),
                custom_estimated_days=node_data.get("custom_estimated_days"),
            )
            db.add(node)
    
    db.commit()
    
    return ResponseModel(message="更新成功")


@router.delete("/{config_id}", response_model=ResponseModel)
def delete_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int = Path(..., ge=1),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除模板配置（软删除）"""
    config = db.query(ProjectTemplateConfig).filter(
        ProjectTemplateConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    config.is_active = False
    db.commit()
    
    return ResponseModel(message="删除成功")
