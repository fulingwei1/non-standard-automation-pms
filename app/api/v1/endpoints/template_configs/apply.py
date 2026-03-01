# -*- coding: utf-8 -*-
"""
应用模板配置创建项目
"""

import json
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project, ProjectMilestone
from app.models.progress import WbsTemplate, WbsTemplateTask
from app.models.project_template_config import ProjectTemplateConfig, StageConfig, NodeConfig
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.post("/{config_id}/create-project", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_from_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    project_code: str = Body(..., description="项目编码"),
    project_name: str = Body(..., description="项目名称"),
    customer_id: Optional[int] = Body(None, description="客户 ID"),
    customer_name: Optional[str] = Body(None, description="客户名称"),
    pm_id: Optional[int] = Body(None, description="项目经理 ID"),
    planned_start_date: Optional[str] = Body(None, description="计划开始日期 YYYY-MM-DD"),
    contract_amount: Optional[float] = Body(None, description="合同金额"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从模板配置创建项目
    根据配置中的启用状态，只创建启用的阶段和节点
    """
    config = get_or_404(db, ProjectTemplateConfig, config_id, detail="配置不存在")
    
    if not config.is_active:
        raise HTTPException(status_code=400, detail="配置已停用")
    
    # 检查项目编码
    existing = db.query(Project).filter(Project.project_code == project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")
    
    start_date = date.fromisoformat(planned_start_date) if planned_start_date else date.today()
    
    # 加载预置模板数据
    from app.services.preset_stage_templates import get_preset_template
    preset_template = get_preset_template(config.base_template_code)
    
    if not preset_template:
        raise HTTPException(status_code=400, detail=f"基础模板 {config.base_template_code} 不存在")
    
    # 创建项目
    project = Project(
        project_code=project_code,
        project_name=project_name,
        project_type=preset_template.get("project_type", "standard"),
        product_category=preset_template.get("product_category"),
        industry=preset_template.get("industry"),
        customer_id=customer_id,
        customer_name=customer_name,
        pm_id=pm_id or current_user.id,
        stage="S1",
        status="ST01",
        health="H1",
        planned_start_date=start_date,
        contract_amount=contract_amount,
        description=config.description,
        budget_amount=0,
        is_active=True,
    )
    
    # 填充 PM 名
    pm = db.query(User).get(project.pm_id)
    if pm:
        project.pm_name = pm.real_name or pm.username
    
    save_obj(db, project)
    
    # 加载配置
    config_data = json.loads(config.config_json) if config.config_json else {}
    stages_config = config_data.get("stages", [])
    
    # 创建阶段和里程碑（只创建启用的）
    milestones_created = 0
    current_day = 0
    
    for stage_cfg in sorted(stages_config, key=lambda s: s.get("sequence", 0)):
        if not stage_cfg.get("is_enabled", True):
            continue  # 跳过禁用的阶段
        
        stage_code = stage_cfg.get("stage_code")
        stage_name = stage_cfg.get("stage_name", "")
        estimated_days = stage_cfg.get("custom_estimated_days") or stage_cfg.get("estimated_days", 7)
        
        # 从预置模板找阶段定义
        stage_def = None
        for s in preset_template.get("stages", []):
            if s.get("stage_code") == stage_code:
                stage_def = s
                break
        
        if not stage_def:
            continue
        
        # 创建里程碑
        milestone = ProjectMilestone(
            project_id=project.id,
            milestone_name=stage_cfg.get("stage_name") or stage_def.get("stage_name", ""),
            milestone_type="STAGE",
            stage_code=stage_code,
            is_key=stage_def.get("is_milestone", False),
            planned_date=start_date + timedelta(days=current_day),
            status="PENDING",
        )
        db.add(milestone)
        milestones_created += 1
        
        # 创建 WBS 任务（只创建启用的节点）
        nodes = stage_cfg.get("nodes", [])
        for node_cfg in sorted(nodes, key=lambda n: n.get("sequence", 0)):
            if not node_cfg.get("is_enabled", True):
                continue  # 跳过禁用的节点
            
            node_code = node_cfg.get("node_code")
            node_name = node_cfg.get("node_name", "")
            node_days = node_cfg.get("custom_estimated_days") or node_cfg.get("estimated_days", 1)
            
            # 从预置模板找节点定义
            node_def = None
            for n in stage_def.get("nodes", []):
                if n.get("node_code") == node_code:
                    node_def = n
                    break
            
            if not node_def:
                continue
            
            # 创建 WBS 任务
            task = WbsTemplateTask(
                template_id=None,  # 直接关联项目
                project_id=project.id,
                task_code=node_code,
                task_name=node_name,
                parent_task_code=None,
                sequence=node_cfg.get("sequence", 0),
                estimated_days=node_days,
                planned_start_date=start_date + timedelta(days=current_day),
                owner_role_code=node_cfg.get("custom_owner_role_code") or node_def.get("owner_role_code", "PM"),
                deliverables=json.dumps(node_def.get("deliverables", [])),
                status="PENDING",
            )
            db.add(task)
        
        current_day += estimated_days
    
    db.commit()
    db.refresh(project)
    
    return ResponseModel(
        message="项目创建成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "milestones_created": milestones_created,
        }
    )
