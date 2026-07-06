# -*- coding: utf-8 -*-
"""
ECN审批适配器

将工程变更(ECN)模块接入统一审批系统
ECN审批较为复杂，包含多部门评估（会签）环节
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.ecn import Ecn, EcnEvaluation
from .base import ApprovalAdapter

# 兼容测试 patch 点；真正使用时在 submit_for_approval 中懒加载，避免循环导入
ApprovalEngineService = None

logger = logging.getLogger(__name__)


class EcnApprovalAdapter(ApprovalAdapter):
    """
    ECN审批适配器

    ECN审批流程特点:
    1. 需要多部门评估（工程、采购、生产、质量等）
    2. 评估结果影响审批决策
    3. 成本影响和工期影响是关键路由条件

    支持的条件字段:
    - entity.ecn_type: ECN类型
    - entity.cost_impact: 成本影响
    - entity.schedule_impact_days: 工期影响(天)
    - entity.priority: 优先级
    - entity.urgency: 紧急程度
    """

    entity_type = "ECN"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[Ecn]:
        """获取ECN实体"""
        return self.db.query(Ecn).filter(Ecn.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取ECN数据用于条件路由

        Returns:
            包含ECN关键数据的字典
        """
        ecn = self.get_entity(entity_id)
        if not ecn:
            return {}

        # 获取评估汇总
        evaluations = self.db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == entity_id).all()

        eval_summary = {
            "total_evaluations": len(evaluations),
            "completed_evaluations": len([e for e in evaluations if e.status == "COMPLETED"]),
            "pending_evaluations": len([e for e in evaluations if e.status == "PENDING"]),
            "total_cost_estimate": sum(float(e.cost_estimate or 0) for e in evaluations),
            "total_schedule_estimate": sum(e.schedule_estimate or 0 for e in evaluations),
            "departments": [e.eval_dept for e in evaluations],
        }

        return {
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "ecn_type": ecn.ecn_type,
            "status": ecn.status,
            "project_id": ecn.project_id,
            "project_code": ecn.project.project_code if ecn.project else None,
            "project_name": ecn.project.project_name if ecn.project else None,
            "machine_id": ecn.machine_id,
            "source_type": ecn.source_type,
            "source_no": ecn.source_no,
            "priority": ecn.priority,
            "urgency": ecn.urgency,
            "cost_impact": float(ecn.cost_impact) if ecn.cost_impact else 0,
            "schedule_impact_days": ecn.schedule_impact_days or 0,
            "quality_impact": ecn.quality_impact,
            "applicant_id": ecn.applicant_id,
            "applicant_name": ecn.applicant.name if ecn.applicant else None,
            "applicant_dept": ecn.applicant_dept,
            "root_cause": ecn.root_cause,
            "root_cause_category": ecn.root_cause_category,
            "evaluation_summary": eval_summary,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        提交审批时的回调

        对于ECN，提交审批意味着开始评估流程
        """
        ecn = self.get_entity(entity_id)
        if ecn:
            ecn.status = "EVALUATING"
            ecn.current_step = "EVALUATION"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批通过时的回调

        ECN审批通过后进入执行阶段
        """
        ecn = self.get_entity(entity_id)
        if ecn:
            ecn.status = "APPROVED"
            ecn.approval_result = "APPROVED"
            ecn.current_step = "EXECUTION"
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批驳回时的回调"""
        ecn = self.get_entity(entity_id)
        if ecn:
            ecn.status = "REJECTED"
            ecn.approval_result = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """撤回审批时的回调"""
        ecn = self.get_entity(entity_id)
        if ecn:
            ecn.status = "DRAFT"
            ecn.current_step = None
            self.db.flush()

    def get_title(self, entity_id: int) -> str:
        """生成审批标题"""
        ecn = self.get_entity(entity_id)
        if ecn:
            return f"ECN审批 - {ecn.ecn_no}: {ecn.ecn_title}"
        return f"ECN审批 - #{entity_id}"

    def get_summary(self, entity_id: int) -> str:
        """生成审批摘要"""
        data = self.get_entity_data(entity_id)
        if not data:
            return ""

        parts = []
        if data.get("ecn_type"):
            parts.append(f"类型: {data['ecn_type']}")
        if data.get("project_name"):
            parts.append(f"项目: {data['project_name']}")
        if data.get("cost_impact"):
            parts.append(f"成本影响: ¥{data['cost_impact']:,.2f}")
        if data.get("schedule_impact_days"):
            parts.append(f"工期影响: {data['schedule_impact_days']}天")
        if data.get("priority"):
            parts.append(f"优先级: {data['priority']}")

        return " | ".join(parts)

    # ========== 高级方法：使用 WorkflowEngine ========== #

    def submit_for_approval(
        self,
        ecn,
        initiator_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        urgency: str = "NORMAL",
        cc_user_ids: Optional[List[int]] = None,
    ) -> ApprovalInstance:
        """
        提交ECN到统一审批引擎

        Args:
            ecn: ECN实例
            initiator_id: 发起人ID
            title: 审批标题
            summary: 审批摘要
            urgency: 紧急程度
            cc_user_ids: 抄送人ID列表

        Returns:
            创建的ApprovalInstance
        """
        # 检查是否已经提交
        if ecn.approval_instance_id:
            logger.warning(f"ECN {ecn.ecn_no} 已经提交审批")
            # 返回现有实例
            return (
                self.db.query(ApprovalInstance)
                .filter(ApprovalInstance.id == ecn.approval_instance_id)
                .first()
            )

        # 构建表单数据
        form_data = {
            "ecn_id": ecn.id,
            "ecn_no": ecn.ecn_no,
            "ecn_title": ecn.ecn_title,
            "ecn_type": ecn.ecn_type,
            "applicant_id": ecn.applicant_id,
            "applicant_name": ecn.applicant_name,
            "project_id": ecn.project_id,
            "impact_analysis": ecn.impact_analysis or "",
        }

        # 添加ECN评估信息
        evaluations = self.db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == ecn.id).all()
        if evaluations:
            form_data["evaluations"] = [
                {
                    "dept": e.eval_dept,
                    "evaluator_id": e.evaluator_id,
                    "evaluator_name": e.evaluator_name,
                    "impact_analysis": e.impact_analysis,
                    "cost_estimate": float(e.cost_estimate) if e.cost_estimate else 0,
                    "schedule_estimate": e.schedule_estimate,
                    "resource_requirement": e.resource_requirement,
                    "risk_assessment": e.risk_assessment,
                    "eval_result": e.eval_result,
                    "eval_opinion": e.eval_opinion,
                    "status": e.status,
                }
                for e in evaluations
            ]

        # 使用统一审批引擎创建实例
        engine_cls = ApprovalEngineService
        if engine_cls is None:
            from ..engine import ApprovalEngineService as engine_cls

        self._ensure_default_approval_template(initiator_id)
        engine = engine_cls(self.db)

        instance = engine.submit(
            template_code="ECN_STANDARD",
            entity_type="ECN",
            entity_id=ecn.id,
            form_data=form_data,
            initiator_id=initiator_id,
            title=title or f"ECN审批 - {ecn.ecn_title}",
            summary=summary or f"{ecn.ecn_type}变更审批：{ecn.ecn_no}",
            urgency=urgency,
            cc_user_ids=cc_user_ids,
        )

        # 更新ECN记录，关联审批实例
        ecn.approval_instance_id = instance.id
        ecn.approval_status = instance.status
        self.db.add(ecn)
        self.db.commit()

        logger.info(f"ECN {ecn.ecn_no} 已提交审批，实例ID: {instance.id}")

        return instance

    def get_approval_status(self, ecn) -> Dict[str, Any]:
        """获取 ECN 审批状态，兼容旧集成测试接口。"""
        instance_id = getattr(ecn, "approval_instance_id", None)
        if not instance_id:
            return {
                "status": "NOT_SUBMITTED",
                "instance_id": None,
                "status_text": "未提交",
                "progress": 0,
            }

        instance = (
            self.db.query(ApprovalInstance)
            .filter(ApprovalInstance.id == instance_id)
            .first()
        )
        status = instance.status if instance else (getattr(ecn, "approval_status", None) or "PENDING")
        status_text = {
            "PENDING": "审批中",
            "IN_PROGRESS": "审批中",
            "APPROVED": "已通过",
            "REJECTED": "已驳回",
            "CANCELLED": "已撤销",
            "TERMINATED": "已终止",
        }.get(status, status or "未知")
        progress = 100 if status in {"APPROVED", "REJECTED", "CANCELLED", "TERMINATED"} else 50
        return {
            "status": status,
            "instance_id": instance_id,
            "status_text": status_text,
            "progress": progress,
        }

    def _ensure_default_approval_template(self, initiator_id: int) -> None:
        """确保空库中存在 ECN 默认审批模板。"""
        template = (
            self.db.query(ApprovalTemplate)
            .filter(ApprovalTemplate.template_code == "ECN_STANDARD")
            .first()
        )
        if not template:
            template = ApprovalTemplate(
                template_code="ECN_STANDARD",
                template_name="ECN标准审批",
                category="BUSINESS",
                entity_type="ECN",
                version=1,
                is_published=True,
                is_active=True,
                created_by=initiator_id,
                published_by=initiator_id,
                form_schema={},
            )
            self.db.add(template)
            self.db.flush()

        flow = (
            self.db.query(ApprovalFlowDefinition)
            .filter(
                ApprovalFlowDefinition.template_id == template.id,
                ApprovalFlowDefinition.is_default,
                ApprovalFlowDefinition.is_active,
            )
            .first()
        )
        if not flow:
            flow = ApprovalFlowDefinition(
                template_id=template.id,
                flow_name="ECN默认审批流",
                is_default=True,
                version=1,
                is_active=True,
                created_by=initiator_id,
            )
            self.db.add(flow)
            self.db.flush()

        node_exists = (
            self.db.query(ApprovalNodeDefinition.id)
            .filter(
                ApprovalNodeDefinition.flow_id == flow.id,
                ApprovalNodeDefinition.is_active,
                ApprovalNodeDefinition.node_type == "APPROVAL",
            )
            .first()
        )
        if not node_exists:
            self.db.add(
                ApprovalNodeDefinition(
                    flow_id=flow.id,
                    node_code="ECN_DEFAULT_APPROVER",
                    node_name="ECN审批",
                    node_order=1,
                    node_type="APPROVAL",
                    approval_mode="SINGLE",
                    is_active=True,
                    approver_type="FIXED_USER",
                    approver_config={"user_ids": [initiator_id]},
                    notify_config={},
                )
            )

        self.db.commit()

    def sync_from_approval_instance(
        self,
        instance: ApprovalInstance,
        ecn,
    ) -> None:
        """
        将ApprovalEngine状态同步回ECN模型

        Args:
            instance: 审批实例
            ecn: ECN实例
        """
        # 同步审批状态
        old_status = ecn.approval_status
        ecn.approval_status = instance.status

        # 根据实例状态更新ECN状态
        if instance.status == "APPROVED":
            ecn.status = "APPROVED"
            ecn.approval_result = "APPROVED"
            ecn.approval_date = instance.completed_at or datetime.now()
            ecn.final_approver_id = instance.final_approver_id
        elif instance.status == "REJECTED":
            ecn.status = "REJECTED"
            ecn.approval_result = "REJECTED"
            ecn.approval_date = instance.completed_at or datetime.now()
        elif instance.status == "CANCELLED":
            ecn.status = "CANCELLED"
            ecn.approval_result = "CANCELLED"
        elif instance.status == "TERMINATED":
            ecn.status = "TERMINATED"
            ecn.approval_result = "TERMINATED"

        # 获取最终审批意见
        if instance.final_comment:
            ecn.approval_note = instance.final_comment

        self.db.add(ecn)
        self.db.flush()

        if instance.status == "APPROVED":
            from app.services.ecn.integration import EcnIntegrationService

            sync_result = EcnIntegrationService(self.db).sync_to_bom_if_ready(ecn.id)
            logger.info(
                "ECN %s 审批通过后自动同步 BOM: %s",
                ecn.ecn_no,
                sync_result,
            )
        else:
            self.db.commit()

        # 如果状态发生变化，记录日志
        if old_status != instance.status:
            logger.info(f"ECN {ecn.ecn_no} 审批状态变化: {old_status} -> {instance.status}")

    def create_ecn_approval_records(
        self,
        instance: ApprovalInstance,
        ecn,
    ) -> List[ApprovalTask]:
        """
        返回统一审批任务，兼容旧集成接口。

        旧版本会把 ApprovalTask 再同步成 `ecn_approvals` 行，造成同一审批
        两套状态。表已退役后，这里只以统一审批任务为准。
        """
        tasks = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == instance.id,
                ApprovalTask.task_type == "APPROVAL",
                ApprovalTask.status == "PENDING",
            )
            .all()
        )
        logger.info("ECN %s 使用统一审批任务 %s 个", ecn.ecn_no, len(tasks))
        return tasks

    def get_ecn_approvers(
        self,
        ecn,
        level: int,
        matrix: Optional[Any] = None,
    ) -> List[int]:
        """
        从统一审批任务获取ECN审批人。

        Args:
            ecn: ECN实例
            level: 审批层级
            matrix: 旧参数，仅保留兼容，不再查询旧矩阵表

        Returns:
            审批人ID列表
        """
        instance_id = getattr(ecn, "approval_instance_id", None)
        if not instance_id:
            instance = (
                self.db.query(ApprovalInstance)
                .filter(
                    ApprovalInstance.entity_type == "ECN",
                    ApprovalInstance.entity_id == ecn.id,
                )
                .order_by(ApprovalInstance.id.desc())
                .first()
            )
            instance_id = instance.id if instance else None
        if not instance_id:
            return []

        tasks = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == instance_id,
                ApprovalTask.task_type == "APPROVAL",
                ApprovalTask.status == "PENDING",
            )
            .all()
        )
        approvers = [
            task.assignee_id
            for task in tasks
            if task.assignee_id and self._determine_approval_level(task.node_id, ecn) == level
        ]
        return list(dict.fromkeys(approvers))

    def _determine_approval_level(
        self,
        node_id: int,
        ecn,
    ) -> int:
        """
        根据节点ID确定ECN审批层级

        简化逻辑：根据node_id的顺序确定层级
        """
        # 获取节点顺序
        node = (
            self.db.query(ApprovalNodeDefinition)
            .filter(ApprovalNodeDefinition.id == node_id)
            .first()
        )

        if not node:
            return 1

        # 使用node_order作为approval_level
        return node.node_order

    def update_ecn_approval_from_action(
        self,
        task: ApprovalTask,
        action: str,
        comment: Optional[str] = None,
    ) -> Optional[ApprovalTask]:
        """
        根据审批操作更新统一审批任务，兼容旧集成接口。

        Args:
            task: 审批任务
            action: 操作（APPROVE/REJECT/WITHDRAW）
            comment: 审批意见

        Returns:
            更新后的 ApprovalTask 实例
        """
        task.action = action
        task.comment = comment
        if action == "APPROVE":
            task.status = "COMPLETED"
            task.completed_at = datetime.now()
        elif action == "REJECT":
            task.status = "COMPLETED"
            task.completed_at = datetime.now()
        elif action == "WITHDRAW":
            task.status = "CANCELLED"
            task.completed_at = datetime.now()

        self.db.add(task)
        self.db.commit()

        logger.info(
            "ECN统一审批任务已更新: task_id=%s, entity_id=%s, action=%s",
            task.id,
            task.instance.entity_id if task.instance else None,
            action,
        )

        return task

    # ========== ECN特有方法 ========== #

    def get_required_evaluators(self, entity_id: int) -> List[Dict[str, Any]]:
        """
        获取ECN需要的评估部门列表

        根据ECN类型确定需要哪些部门进行评估
        """
        ecn = self.get_entity(entity_id)
        if not ecn:
            return []

        # 基础评估部门（所有ECN都需要）
        base_depts = [
            {"dept": "工程部", "required": True},
        ]

        # 根据ECN类型添加额外评估部门
        ecn_type = ecn.ecn_type
        if ecn_type in ("MATERIAL", "SUPPLIER"):
            base_depts.append({"dept": "采购部", "required": True})

        if ecn_type in ("PROCESS", "MATERIAL"):
            base_depts.append({"dept": "生产部", "required": True})

        if ecn_type in ("DESIGN", "SPEC"):
            base_depts.append({"dept": "质量部", "required": True})

        # 成本影响较大时需要财务评估
        if ecn.cost_impact and ecn.cost_impact > 10000:
            base_depts.append({"dept": "财务部", "required": True})

        return base_depts

    def create_evaluation_tasks(
        self,
        entity_id: int,
        instance: ApprovalInstance,
    ) -> List[EcnEvaluation]:
        """
        创建ECN评估任务

        在审批流程开始时，为各部门创建评估任务
        """
        evaluators = self.get_required_evaluators(entity_id)
        evaluations = []

        for eval_info in evaluators:
            evaluation = EcnEvaluation(
                ecn_id=entity_id,
                eval_dept=eval_info["dept"],
                status="PENDING",
            )
            self.db.add(evaluation)
            evaluations.append(evaluation)

        self.db.flush()
        return evaluations

    def check_evaluation_complete(self, entity_id: int) -> tuple[bool, Dict[str, Any]]:
        """
        检查评估是否全部完成

        Returns:
            (是否完成, 评估汇总数据)
        """
        evaluations = self.db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == entity_id).all()

        if not evaluations:
            return False, {}

        pending = [e for e in evaluations if e.status == "PENDING"]
        completed = [e for e in evaluations if e.status == "COMPLETED"]

        summary = {
            "total": len(evaluations),
            "pending": len(pending),
            "completed": len(completed),
            "pending_depts": [e.eval_dept for e in pending],
            "total_cost": sum(float(e.cost_estimate or 0) for e in completed),
            "total_days": sum(e.schedule_estimate or 0 for e in completed),
            "all_approved": all(e.eval_result == "APPROVE" for e in completed),
        }

        return len(pending) == 0, summary
