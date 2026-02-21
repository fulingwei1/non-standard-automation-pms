# -*- coding: utf-8 -*-
"""
ECN审批适配器

将工程变更(ECN)模块接入统一审批系统
ECN审批较为复杂，包含多部门评估（会签）环节
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.ecn import Ecn, EcnEvaluation, EcnApproval

from .base import ApprovalAdapter



from datetime import datetime, timedelta
from app.schemas.approval.instance import ApprovalInstanceCreate
from app.models.user import UserRole
from app.models.user import User
from app.models.user import Role
from app.models.ecn import EcnApprovalMatrix
from app.models.approval import ApprovalNodeDefinition
import logging

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
        evaluations = self.db.query(EcnEvaluation).filter(
            EcnEvaluation.ecn_id == entity_id
        ).all()

        eval_summary = {
            "total_evaluations": len(evaluations),
            "completed_evaluations": len([e for e in evaluations if e.status == "COMPLETED"]),
            "pending_evaluations": len([e for e in evaluations if e.status == "PENDING"]),
            "total_cost_estimate": sum(
                float(e.cost_estimate or 0) for e in evaluations
            ),
            "total_schedule_estimate": sum(
                e.schedule_estimate or 0 for e in evaluations
            ),
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
        evaluations = (
            self.db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == ecn.id).all()
        )
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
        
        # 创建审批实例
        ApprovalInstanceCreate(
            template_code="ECN_STANDARD",
            entity_type="ECN",
            entity_id=ecn.id,
            form_data=form_data,
            title=title or f"ECN审批 - {ecn.ecn_title}",
            summary=summary or f"{ecn.ecn_type}变更审批：{ecn.ecn_no}",
            urgency=urgency,
            cc_user_ids=cc_user_ids,
        )
        
        # 使用统一引擎创建实例
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        
        workflow_engine = WorkflowEngine(self.db)
        
        instance = workflow_engine.create_instance(
            flow_code="ECN_STANDARD",
            business_type="ECN",
            business_id=ecn.id,
            business_title=ecn.ecn_title,
            submitted_by=initiator_id,
            config={"ecn": form_data},
        )
        
        # 更新ECN记录，关联审批实例
        ecn.approval_instance_id = instance.id
        ecn.approval_status = instance.status
        self.db.add(ecn)
        self.db.commit()
        
        logger.info(f"ECN {ecn.ecn_no} 已提交审批，实例ID: {instance.id}")
        
        return instance
    
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
        self.db.commit()
        
        # 如果状态发生变化，记录日志
        if old_status != instance.status:
            logger.info(
                f"ECN {ecn.ecn_no} 审批状态变化: {old_status} -> {instance.status}"
            )
    
    def create_ecn_approval_records(
        self,
        instance: ApprovalInstance,
        ecn,
    ) -> List[EcnApproval]:
        """
        根据审批实例创建ECN审批记录
        
        将ApprovalEngine的任务转换为ECN的审批记录
        """
        from app.models.ecn import EcnApproval
        
        # 获取当前节点对应的审批任务
        tasks = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == instance.id,
                ApprovalTask.status == "PENDING",
            )
            .all()
        )
        
        approval_records = []
        
        for task in tasks:
            # 确定审批层级
            approval_level = self._determine_approval_level(task.node_id, ecn)
            
            # 获取审批人
            if task.assignee_id:
                approver = (
                    self.db.query(User).filter(User.id == task.assignee_id).first()
                )
            else:
                approver = None
            
            # 创建或更新EcnApproval记录
            existing_approval = (
                self.db.query(EcnApproval)
                .filter(
                    EcnApproval.ecn_id == ecn.id,
                    EcnApproval.approval_level == approval_level,
                )
                .first()
            )
            
            # 计算到期时间
            due_date = task.due_at or (datetime.now() + timedelta(hours=48))
            
            if existing_approval:
                # 更新现有记录
                existing_approval.approver_id = task.assignee_id
                existing_approval.approver_name = approver.real_name if approver else ""
                existing_approval.approval_result = None  # 待审批
                existing_approval.status = "PENDING"
                existing_approval.due_date = due_date
                existing_approval.is_overdue = False
                
                self.db.add(existing_approval)
                approval_records.append(existing_approval)
            else:
                # 创建新记录
                approval = EcnApproval(
                    ecn_id=ecn.id,
                    approval_level=approval_level,
                    approval_role=task.node_name or "",
                    approver_id=task.assignee_id,
                    approver_name=approver.real_name if approver else "",
                    approval_result=None,  # 待审批
                    status="PENDING",
                    due_date=due_date,
                    is_overdue=False,
                )
                
                self.db.add(approval)
                approval_records.append(approval)
        
        self.db.commit()
        
        logger.info(f"为ECN {ecn.ecn_no} 创建了 {len(approval_records)} 个审批记录")
        
        return approval_records
    
    def get_ecn_approvers(
        self,
        ecn,
        level: int,
        matrix: Optional[EcnApprovalMatrix] = None,
    ) -> List[int]:
        """
        根据审批矩阵获取ECN审批人
        
        Args:
            ecn: ECN实例
            level: 审批层级
            matrix: 审批矩阵配置
        
        Returns:
            审批人ID列表
        """
        if not matrix:
            # 从数据库查询审批矩阵
            matrix = (
                self.db.query(EcnApprovalMatrix)
                .filter(
                    EcnApprovalMatrix.ecn_type == ecn.ecn_type,
                    EcnApprovalMatrix.approval_level == level,
                    EcnApprovalMatrix.is_active,
                )
                .all()
            )
        
        approvers = []
        
        for matrix_item in matrix:
            # 根据审批角色查找用户
            if matrix_item.approval_role:
                users = (
                    self.db.query(User.id)
                    .join(UserRole, User.id == UserRole.user_id)
                    .join(Role, UserRole.role_id == Role.id)
                    .filter(
                        Role.role_code == matrix_item.approval_role,
                        User.is_active,
                    )
                    .all()
                )
                approvers.extend([u.id for u in users])
        
        # 去重
        return list(set(approvers))
    
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
    ) -> Optional[EcnApproval]:
        """
        根据审批操作更新ECN审批记录
        
        Args:
            task: 审批任务
            action: 操作（APPROVE/REJECT/WITHDRAW）
            comment: 审批意见
        
        Returns:
            更新后的EcnApproval实例
        """
        # 获取ECN审批记录
        approval_level = self._determine_approval_level(
            task.node_id, task.instance.entity
        )
        approval = (
            self.db.query(EcnApproval)
            .filter(
                EcnApproval.ecn_id == task.instance.entity_id,
                EcnApproval.approval_level == approval_level,
            )
            .first()
        )
        
        if not approval:
            logger.warning(
                f"未找到ECN审批记录: entity_id={task.instance.entity_id}, level={approval_level}"
            )
            return None
        
        # 更新审批结果
        if action == "APPROVE":
            approval.approval_result = "APPROVED"
            approval.approval_opinion = comment
            approval.status = "APPROVED"
            approval.approved_at = datetime.now()
        elif action == "REJECT":
            approval.approval_result = "REJECTED"
            approval.approval_opinion = comment
            approval.status = "REJECTED"
            approval.approved_at = datetime.now()
        elif action == "WITHDRAW":
            approval.approval_result = "WITHDRAWN"
            approval.status = "CANCELLED"
        
        self.db.add(approval)
        self.db.commit()
        
        logger.info(
            f"ECN审批记录已更新: entity_id={approval.ecn_id}, level={approval.approval_level}, action={action}"
        )
        
        return approval
    
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
        evaluations = self.db.query(EcnEvaluation).filter(
            EcnEvaluation.ecn_id == entity_id
        ).all()

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
