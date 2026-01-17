# -*- coding: utf-8 -*-
"""
ECN模块集成/同步 API endpoints

包含：同步到BOM、同步到项目、同步到采购、批量操作
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnAffectedMaterial, EcnAffectedOrder, EcnTask
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.ecn import EcnTaskCreate
from app.services.ecn_auto_assign_service import auto_assign_task
from app.services.ecn_notification_service import notify_task_assigned

router = APIRouter()


@router.post("/ecns/{ecn_id}/sync-to-bom", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_bom(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到BOM
    根据受影响物料自动更新BOM
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    if ecn.status != "APPROVED" and ecn.status != "EXECUTING":
        raise HTTPException(status_code=400, detail="只能同步已审批或执行中的ECN")

    affected_materials = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id,
        EcnAffectedMaterial.status == "PENDING"
    ).all()

    updated_count = 0
    for am in affected_materials:
        if am.bom_item_id:
            from app.models.material import BomItem
            bom_item = db.query(BomItem).filter(BomItem.id == am.bom_item_id).first()
            if bom_item:
                # 根据变更类型更新BOM
                if am.change_type == "UPDATE":
                    if am.new_quantity:
                        bom_item.qty = float(am.new_quantity)
                    if am.new_specification:
                        bom_item.specification = am.new_specification
                elif am.change_type == "REPLACE" and am.material_id:
                    bom_item.material_id = am.material_id

                am.status = "PROCESSED"
                am.processed_at = datetime.now()
                db.add(bom_item)
                db.add(am)
                updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"已同步{updated_count}个物料变更到BOM",
        data={"updated_count": updated_count}
    )


@router.post("/ecns/{ecn_id}/sync-to-project", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_project(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到项目
    更新项目成本和工期
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    if not ecn.project_id:
        raise HTTPException(status_code=400, detail="ECN未关联项目")

    project = db.query(Project).filter(Project.id == ecn.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 更新项目成本（累加ECN的成本影响）
    if ecn.cost_impact:
        project.total_cost = (project.total_cost or Decimal("0")) + ecn.cost_impact

    # 更新项目工期（累加ECN的工期影响）
    if ecn.schedule_impact_days:
        # 这里需要根据项目的实际工期计算逻辑来更新
        # 示例：更新项目结束日期
        if project.planned_end_date:
            project.planned_end_date = project.planned_end_date + timedelta(days=ecn.schedule_impact_days)

    db.add(project)
    db.commit()

    return ResponseModel(
        code=200,
        message="ECN变更已同步到项目",
        data={
            "cost_impact": float(ecn.cost_impact or 0),
            "schedule_impact_days": ecn.schedule_impact_days or 0
        }
    )


@router.post("/ecns/{ecn_id}/sync-to-purchase", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_purchase(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到采购订单
    根据受影响订单自动更新采购订单状态
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    affected_orders = db.query(EcnAffectedOrder).filter(
        EcnAffectedOrder.ecn_id == ecn_id,
        EcnAffectedOrder.order_type == "PURCHASE",
        EcnAffectedOrder.status == "PENDING"
    ).all()

    updated_count = 0
    for ao in affected_orders:
        from app.models.purchase import PurchaseOrder
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
        if order:
            # 根据处理方式更新订单
            if ao.action_type == "CANCEL":
                order.status = "CANCELLED"
            elif ao.action_type == "MODIFY":
                # 这里可以添加更详细的订单修改逻辑
                pass

            ao.status = "PROCESSED"
            ao.processed_by = current_user.id
            ao.processed_at = datetime.now()
            db.add(order)
            db.add(ao)
            updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"已同步{updated_count}个采购订单变更",
        data={"updated_count": updated_count}
    )


# ==================== 批量操作 ====================

@router.post("/ecns/batch-sync-to-bom", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_bom(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到BOM
    """
    results = []
    success_count = 0
    fail_count = 0

    for ecn_id in ecn_ids:
        try:
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                fail_count += 1
                continue

            if ecn.status != "APPROVED" and ecn.status != "EXECUTING":
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "只能同步已审批或执行中的ECN"})
                fail_count += 1
                continue

            # 调用单个同步逻辑
            affected_materials = db.query(EcnAffectedMaterial).filter(
                EcnAffectedMaterial.ecn_id == ecn_id,
                EcnAffectedMaterial.status == "PENDING"
            ).all()

            updated_count = 0
            for am in affected_materials:
                if am.bom_item_id:
                    from app.models.material import BomItem
                    bom_item = db.query(BomItem).filter(BomItem.id == am.bom_item_id).first()
                    if bom_item:
                        if am.change_type == "UPDATE":
                            if am.new_quantity:
                                bom_item.qty = float(am.new_quantity)
                            if am.new_specification:
                                bom_item.specification = am.new_specification
                        elif am.change_type == "REPLACE" and am.material_id:
                            bom_item.material_id = am.material_id

                        am.status = "PROCESSED"
                        am.processed_at = datetime.now()
                        db.add(bom_item)
                        db.add(am)
                        updated_count += 1

            db.commit()
            results.append({
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "status": "success",
                "updated_count": updated_count
            })
            success_count += 1
        except Exception as e:
            db.rollback()
            results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
            fail_count += 1

    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{success_count}个，失败{fail_count}个",
        data={
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )


@router.post("/ecns/batch-sync-to-project", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_project(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到项目
    """
    results = []
    success_count = 0
    fail_count = 0

    for ecn_id in ecn_ids:
        try:
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                fail_count += 1
                continue

            if not ecn.project_id:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN未关联项目"})
                fail_count += 1
                continue

            project = db.query(Project).filter(Project.id == ecn.project_id).first()
            if not project:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "项目不存在"})
                fail_count += 1
                continue

            # 更新项目成本
            if ecn.cost_impact:
                project.total_cost = (project.total_cost or Decimal("0")) + ecn.cost_impact

            # 更新项目工期
            if ecn.schedule_impact_days and project.planned_end_date:
                project.planned_end_date = project.planned_end_date + timedelta(days=ecn.schedule_impact_days)

            db.add(project)
            db.commit()

            results.append({
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "project_id": ecn.project_id,
                "status": "success",
                "cost_impact": float(ecn.cost_impact or 0),
                "schedule_impact_days": ecn.schedule_impact_days or 0
            })
            success_count += 1
        except Exception as e:
            db.rollback()
            results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
            fail_count += 1

    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{success_count}个，失败{fail_count}个",
        data={
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )


@router.post("/ecns/batch-sync-to-purchase", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_purchase(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到采购
    """
    results = []
    success_count = 0
    fail_count = 0

    for ecn_id in ecn_ids:
        try:
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                fail_count += 1
                continue

            affected_orders = db.query(EcnAffectedOrder).filter(
                EcnAffectedOrder.ecn_id == ecn_id,
                EcnAffectedOrder.order_type == "PURCHASE",
                EcnAffectedOrder.status == "PENDING"
            ).all()

            updated_count = 0
            for ao in affected_orders:
                from app.models.purchase import PurchaseOrder
                order = db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
                if order:
                    if ao.action_type == "CANCEL":
                        order.status = "CANCELLED"
                    elif ao.action_type == "MODIFY":
                        pass  # 可以添加更详细的订单修改逻辑

                    ao.status = "PROCESSED"
                    ao.processed_by = current_user.id
                    ao.processed_at = datetime.now()
                    db.add(order)
                    db.add(ao)
                    updated_count += 1

            db.commit()

            results.append({
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "status": "success",
                "updated_count": updated_count
            })
            success_count += 1
        except Exception as e:
            db.rollback()
            results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
            fail_count += 1

    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{success_count}个，失败{fail_count}个",
        data={
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )


@router.post("/ecns/{ecn_id}/batch-create-tasks", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_create_ecn_tasks(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    tasks: List[EcnTaskCreate] = Body(..., description="任务列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量创建ECN执行任务
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    if ecn.status not in ["APPROVED", "EXECUTING"]:
        raise HTTPException(status_code=400, detail="ECN当前不在执行阶段")

    # 获取最大任务序号
    max_order = db.query(EcnTask).filter(EcnTask.ecn_id == ecn_id).order_by(desc(EcnTask.task_no)).first()
    start_no = (max_order.task_no + 1) if max_order else 1

    created_tasks = []
    for idx, task_in in enumerate(tasks):
        task = EcnTask(
            ecn_id=ecn_id,
            task_no=start_no + idx,
            task_name=task_in.task_name,
            task_type=task_in.task_type,
            task_dept=task_in.task_dept,
            task_description=task_in.task_description,
            assignee_id=task_in.assignee_id,
            planned_start=task_in.planned_start,
            planned_end=task_in.planned_end,
            status="PENDING",
            progress_pct=0
        )

        # 如果没有指定负责人，自动分配
        if not task.assignee_id:
            try:
                assignee_id = auto_assign_task(db, ecn, task)
                if assignee_id:
                    task.assignee_id = assignee_id
            except Exception as e:
                logger.error(f"Failed to auto assign task: {e}")

        db.add(task)
        created_tasks.append(task)

        # 发送通知
        if task.assignee_id:
            try:
                notify_task_assigned(db, ecn, task, task.assignee_id)
            except Exception as e:
                logger.error(f"Failed to send task assigned notification: {e}")

    # 如果ECN状态是已审批，自动更新为执行中
    if ecn.status == "APPROVED":
        ecn.status = "EXECUTING"
        ecn.execution_start = datetime.now()
        ecn.current_step = "EXECUTION"
        db.add(ecn)

    db.commit()

    # 刷新任务以获取ID
    for task in created_tasks:
        db.refresh(task)

    return ResponseModel(
        code=200,
        message=f"批量创建任务成功：共{len(created_tasks)}个",
        data={
            "ecn_id": ecn_id,
            "created_count": len(created_tasks),
            "task_ids": [task.id for task in created_tasks]
        }
    )
