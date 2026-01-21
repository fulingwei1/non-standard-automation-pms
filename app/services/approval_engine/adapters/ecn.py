# -*- coding: utf-8 -*-
"""
ECN审批适配器

将工程变更(ECN)模块接入统一审批系统
ECN审批较为复杂，包含多部门评估（会签）环节
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
from app.models.ecn import Ecn, EcnEvaluation

from .base import ApprovalAdapter


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

    def validate_submit(self, entity_id: int) -> tuple[bool, str]:
        """验证是否可以提交审批"""
        ecn = self.get_entity(entity_id)
        if not ecn:
            return False, "ECN不存在"

        if ecn.status not in ("DRAFT", "REJECTED"):
            return False, f"当前状态({ecn.status})不允许提交审批"

        if not ecn.change_reason:
            return False, "请填写变更原因"

        if not ecn.change_description:
            return False, "请填写变更描述"

        return True, ""

    # ==================== ECN特有方法 ====================

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

    def create_evaluation_tasks(self, entity_id: int, instance: ApprovalInstance) -> List[EcnEvaluation]:
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
