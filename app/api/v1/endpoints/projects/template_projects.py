# -*- coding: utf-8 -*-
"""
项目模板 - 从模板创建项目（含WBS任务+里程碑自动生成）
"""

import json
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project, ProjectMilestone, ProjectTemplate, ProjectTemplateVersion
from app.models.progress import WbsTemplate, WbsTemplateTask
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.post("/templates/{template_id}/create-project", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_from_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    project_code: str = Body(..., description="项目编码"),
    project_name: str = Body(..., description="项目名称"),
    customer_id: Optional[int] = Body(None, description="客户ID"),
    customer_name: Optional[str] = Body(None, description="客户名称"),
    pm_id: Optional[int] = Body(None, description="项目经理ID"),
    planned_start_date: Optional[str] = Body(None, description="计划开始日期 YYYY-MM-DD"),
    planned_end_date: Optional[str] = Body(None, description="计划结束日期 YYYY-MM-DD"),
    contract_amount: Optional[float] = Body(None, description="合同金额"),
    create_milestones: bool = Body(True, description="是否创建里程碑"),
    create_wbs: bool = Body(True, description="是否创建WBS任务"),
    version_id: Optional[int] = Body(None, description="版本ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从模板创建项目，自动生成：
    1. 项目基本信息（继承模板类型、行业等）
    2. 里程碑（从模板配置生成，基于开始日期自动计算）
    3. WBS任务（从WBS模板生成，自动排期）
    """
    template = get_or_404(db, ProjectTemplate, template_id, detail="模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已停用")

    # 检查项目编码
    existing = db.query(Project).filter(Project.project_code == project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")

    start_date = date.fromisoformat(planned_start_date) if planned_start_date else date.today()
    end_date = date.fromisoformat(planned_end_date) if planned_end_date else None

    # 解析模板配置
    config = {}
    if template.template_config:
        try:
            config = json.loads(template.template_config) if isinstance(template.template_config, str) else template.template_config
        except (json.JSONDecodeError, TypeError):
            pass

    # 也检查版本配置
    version_config = {}
    if version_id:
        version = db.query(ProjectTemplateVersion).filter(
            ProjectTemplateVersion.id == version_id,
            ProjectTemplateVersion.template_id == template_id
        ).first()
        if version and version.config:
            version_config = version.config if isinstance(version.config, dict) else {}

    # 创建项目
    project = Project(
        project_code=project_code,
        project_name=project_name,
        project_type=template.project_type or "standard",
        product_category=template.product_category,
        industry=template.industry,
        customer_id=customer_id,
        customer_name=customer_name,
        pm_id=pm_id or current_user.id,
        stage="S1",
        status="ST01",
        health="H1",
        planned_start_date=start_date,
        planned_end_date=end_date,
        contract_amount=contract_amount,
        description=template.description,
        budget_amount=0,
        is_active=True,
    )

    # 填充 PM 名
    pm = db.query(User).get(project.pm_id)
    if pm:
        project.pm_name = pm.real_name or pm.username

    # 填充客户信息
    if customer_id and not customer_name:
        try:
            from app.models.project import Customer
            customer = db.query(Customer).get(customer_id)
            if customer:
                project.customer_name = customer.customer_name
        except Exception:
            pass

    save_obj(db, project)

    milestones_created = 0
    tasks_created = 0

    # ========== 创建里程碑 ==========
    if create_milestones:
        # 优先用 template_config 中的里程碑
        milestone_defs = config.get("milestones", [])
        for m_def in milestone_defs:
            if isinstance(m_def, (list, tuple)) and len(m_def) >= 5:
                name, m_type, stage_code, is_key, offset = m_def
                milestone = ProjectMilestone(
                    project_id=project.id,
                    milestone_name=name,
                    milestone_type=m_type,
                    stage_code=stage_code,
                    is_key=is_key,
                    planned_date=start_date + timedelta(days=offset),
                    status="PENDING",
                )
                db.add(milestone)
                milestones_created += 1

        # 也检查版本配置中的里程碑（dict格式）
        if not milestone_defs and version_config.get("milestones"):
            for mc in version_config["milestones"]:
                milestone = ProjectMilestone(
                    project_id=project.id,
                    milestone_name=mc.get("milestone_name", ""),
                    milestone_type=mc.get("milestone_type", ""),
                    stage_code=mc.get("stage", "S1"),
                    is_key=mc.get("is_key", False),
                )
                db.add(milestone)
                milestones_created += 1

    # ========== 创建 WBS 任务 ==========
    if create_wbs:
        wbs_code = config.get("wbs_template_code")
        if wbs_code:
            wbs_template = db.query(WbsTemplate).filter(WbsTemplate.template_code == wbs_code).first()
            if wbs_template:
                tasks = db.query(WbsTemplateTask).filter(
                    WbsTemplateTask.template_id == wbs_template.id
                ).order_by(WbsTemplateTask.id).all()

                cumulative_days = 0
                for task in tasks:
                    try:
                        from datetime import datetime as _dt
                        now_str = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
                        db.execute(text("""
                            INSERT INTO tasks 
                            (project_id, task_name, stage, weight,
                             plan_start, plan_end, status, progress_percent, created_at, updated_at)
                            VALUES (:pid, :name, :stage, :weight,
                                    :start, :end, 'pending', 0, :now, :now)
                        """), {
                            "pid": project.id,
                            "name": task.task_name,
                            "stage": task.stage,
                            "weight": float(task.weight) if task.weight else 1.0,
                            "start": (start_date + timedelta(days=cumulative_days)).isoformat(),
                            "end": (start_date + timedelta(days=cumulative_days + (task.plan_days or 0))).isoformat(),
                            "now": now_str,
                        })
                        tasks_created += 1
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Failed to create task '{task.task_name}': {e}")
                        break
                    cumulative_days += task.plan_days or 0

    # 复制版本配置中的机台
    if version_config.get("machines"):
        for mc in version_config["machines"]:
            machine = Machine(
                project_id=project.id,
                machine_code=mc.get("machine_code", f"PN{project.id:03d}"),
                machine_name=mc.get("machine_name", ""),
                machine_type=mc.get("machine_type", ""),
                status="PENDING",
                progress_pct=0,
            )
            db.add(machine)

    # Commit project + milestones + tasks first
    db.commit()

    # 初始化标准阶段 (separate transaction)
    try:
        from app.utils.project_utils import init_project_stages
        init_project_stages(db, project.id)
        db.commit()
    except Exception:
        db.rollback()

    # 更新模板使用次数
    try:
        db.execute(text("UPDATE project_templates SET usage_count = COALESCE(usage_count, 0) + 1 WHERE id = :tid"), {"tid": template_id})
        db.commit()
    except Exception:
        db.rollback()

    return ResponseModel(
        code=201,
        message="从模板创建项目成功",
        data={
            "id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "template_id": template_id,
            "template_name": template.template_name,
            "milestones_created": milestones_created,
            "tasks_created": tasks_created,
        }
    )
