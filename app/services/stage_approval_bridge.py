# -*- coding: utf-8 -*-
"""
阶段特批桥接服务

当阶段门校验未通过时，解析出对应的审批入口参数，
让前端知道"去哪里发起特批"，而不只是"需要特批"。

复用现有审批引擎（ApprovalTemplate + ApprovalFlowDefinition），
不新造审批系统。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTemplate

logger = logging.getLogger(__name__)


# ==================== 阶段→审批模板映射配置 ====================
# key: (from_stage, to_stage)
# value: 审批场景列表，每个场景包含 condition_tag（对应 missing_item 关键词）和审批参数
#
# 这个映射可以后续迁移到数据库配置表，当前先硬编码保证可用。

STAGE_APPROVAL_MAP: Dict[str, List[Dict[str, Any]]] = {
    "S3->S4": [
        {
            "condition_tag": "合同",
            "approval_type": "STAGE_GATE_OVERRIDE",
            "approval_hint": "合同未签订，需发起立项特批",
            "template_code": "PROJECT_STAGE_OVERRIDE",
            "entity_type": "PROJECT",
            "urgency": "URGENT",
            "form_fields_hint": {
                "override_reason": "合同尚未签订，申请特批推进至方案设计阶段",
                "risk_assessment": "请说明无合同推进的风险和应对措施",
            },
        },
    ],
    "S4->S5": [
        {
            "condition_tag": "BOM",
            "approval_type": "STAGE_GATE_OVERRIDE",
            "approval_hint": "BOM未发布，需发起设计评审特批",
            "template_code": "PROJECT_STAGE_OVERRIDE",
            "entity_type": "PROJECT",
            "urgency": "URGENT",
            "form_fields_hint": {
                "override_reason": "BOM尚未发布，申请特批推进至采购制造阶段",
                "risk_assessment": "请说明BOM未完成时推进的风险",
            },
        },
    ],
    "S5->S6": [
        {
            "condition_tag": "物料",
            "approval_type": "STAGE_GATE_OVERRIDE",
            "approval_hint": "物料齐套率不足，需发起采购特批",
            "template_code": "PURCHASE_EXCEPTION",
            "entity_type": "PROJECT",
            "urgency": "URGENT",
            "form_fields_hint": {
                "override_reason": "关键物料齐套率未达标，申请特批推进至装配联调",
                "shortage_detail": "请列出缺料明细及预计到货时间",
            },
        },
    ],
    "S7->S8": [
        {
            "condition_tag": "FAT",
            "approval_type": "STAGE_GATE_OVERRIDE",
            "approval_hint": "FAT验收未通过，需发起出厂特批",
            "template_code": "PROJECT_STAGE_OVERRIDE",
            "entity_type": "PROJECT",
            "urgency": "CRITICAL",
            "form_fields_hint": {
                "override_reason": "FAT验收未完成，申请特批推进至现场交付",
                "customer_agreement": "请上传客户同意先行发货的确认函",
            },
        },
    ],
    "S8->S9": [
        {
            "condition_tag": "终验收",
            "approval_type": "STAGE_GATE_OVERRIDE",
            "approval_hint": "终验收未通过，需发起结项特批",
            "template_code": "PROJECT_STAGE_OVERRIDE",
            "entity_type": "PROJECT",
            "urgency": "CRITICAL",
            "form_fields_hint": {
                "override_reason": "终验收未完成，申请特批结项",
                "pending_items": "请说明遗留事项及处理计划",
            },
        },
        {
            "condition_tag": "回款",
            "approval_type": "STAGE_GATE_OVERRIDE",
            "approval_hint": "回款率未达标，需发起财务特批",
            "template_code": "FINANCE_EXCEPTION",
            "entity_type": "PROJECT",
            "urgency": "URGENT",
            "form_fields_hint": {
                "override_reason": "回款率未达80%，申请特批结项",
                "collection_plan": "请附回款计划及预计到账时间",
            },
        },
    ],
}


class StageApprovalBridge:
    """
    阶段特批桥接器

    职责：
    1. 根据阶段门校验的失败项，匹配对应的审批模板
    2. 生成完整的特批入口参数（template_code, action_url, form_data 预填）
    3. 检查是否已有进行中的特批单
    """

    def __init__(self, db: Session):
        self.db = db

    def resolve(
        self,
        project_id: int,
        from_stage: str,
        to_stage: str,
        missing_items: List[str],
    ) -> List[Dict[str, Any]]:
        """
        根据阶段流转和缺失项，解析出可用的特批入口列表。

        Returns:
            特批入口列表，每项包含：
            - approval_type: 特批类型标识
            - approval_hint: 人可读的提示（如"合同未签订，需发起立项特批"）
            - template_code: 审批模板编码
            - entity_type: 业务实体类型
            - action_url: 前端跳转的审批发起URL
            - form_data_prefill: 预填的表单数据
            - existing_instance: 如果已有进行中的特批单，返回其信息
        """
        transition_key = f"{from_stage}->{to_stage}"
        candidates = STAGE_APPROVAL_MAP.get(transition_key, [])

        if not candidates:
            return []

        missing_text = " ".join(missing_items)
        bridges = []

        for candidate in candidates:
            tag = candidate["condition_tag"]
            if tag not in missing_text:
                continue

            template_code = candidate["template_code"]

            # 检查模板是否存在
            template_exists = self._check_template_exists(template_code)

            # 构建 action_url
            action_url = self._build_action_url(
                template_code=template_code,
                entity_type=candidate["entity_type"],
                project_id=project_id,
                from_stage=from_stage,
                to_stage=to_stage,
            )

            # 构建预填表单数据
            form_data_prefill = {
                "project_id": project_id,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "gate_missing_items": missing_items,
                **candidate.get("form_fields_hint", {}),
            }

            # 查找进行中的特批单
            existing = self._find_pending_instance(
                template_code=template_code,
                entity_type=candidate["entity_type"],
                entity_id=project_id,
            )

            bridge_entry = {
                "approval_type": candidate["approval_type"],
                "approval_hint": candidate["approval_hint"],
                "template_code": template_code,
                "template_exists": template_exists,
                "entity_type": candidate["entity_type"],
                "urgency": candidate.get("urgency", "NORMAL"),
                "action_url": action_url,
                "form_data_prefill": form_data_prefill,
                "existing_instance": existing,
            }
            bridges.append(bridge_entry)

        # 如果没有匹配到具体场景，但确实有缺失项，提供通用特批入口
        if not bridges and missing_items:
            bridges.append(self._build_generic_bridge(project_id, from_stage, to_stage, missing_items))

        return bridges

    def check_approval_granted(
        self,
        project_id: int,
        from_stage: str,
        to_stage: str,
    ) -> Optional[Dict[str, Any]]:
        """
        检查是否已有通过的特批单（可在阶段推进时用来放行）。

        Returns:
            如果有已通过的特批，返回 {"approved": True, "instance_no": ..., "approved_at": ...}
            否则返回 None
        """
        transition_key = f"{from_stage}->{to_stage}"
        candidates = STAGE_APPROVAL_MAP.get(transition_key, [])

        for candidate in candidates:
            instance = (
                self.db.query(ApprovalInstance)
                .filter(
                    ApprovalInstance.entity_type == candidate["entity_type"],
                    ApprovalInstance.entity_id == project_id,
                    ApprovalInstance.status == "APPROVED",
                )
                .join(ApprovalTemplate, ApprovalInstance.template_id == ApprovalTemplate.id)
                .filter(ApprovalTemplate.template_code == candidate["template_code"])
                .order_by(ApprovalInstance.completed_at.desc())
                .first()
            )

            if instance:
                return {
                    "approved": True,
                    "instance_no": instance.instance_no,
                    "instance_id": instance.id,
                    "approved_at": instance.completed_at.isoformat() if instance.completed_at else None,
                    "approval_type": candidate["approval_type"],
                }

        return None

    def _check_template_exists(self, template_code: str) -> bool:
        """检查审批模板是否已配置"""
        return (
            self.db.query(ApprovalTemplate)
            .filter(
                ApprovalTemplate.template_code == template_code,
                ApprovalTemplate.is_active,
            )
            .first()
            is not None
        )

    def _build_action_url(
        self,
        template_code: str,
        entity_type: str,
        project_id: int,
        from_stage: str,
        to_stage: str,
    ) -> str:
        """
        构建审批发起URL。

        前端拿到此URL后可直接跳转到审批发起页面，
        query params 里带了预填信息。
        """
        return (
            f"/approval/submit"
            f"?template_code={template_code}"
            f"&entity_type={entity_type}"
            f"&entity_id={project_id}"
            f"&source=stage_gate"
            f"&from_stage={from_stage}"
            f"&to_stage={to_stage}"
        )

    def _find_pending_instance(
        self,
        template_code: str,
        entity_type: str,
        entity_id: int,
    ) -> Optional[Dict[str, Any]]:
        """查找已有的进行中特批单"""
        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == entity_type,
                ApprovalInstance.entity_id == entity_id,
                ApprovalInstance.status.in_(["PENDING", "DRAFT"]),
            )
            .join(ApprovalTemplate, ApprovalInstance.template_id == ApprovalTemplate.id)
            .filter(ApprovalTemplate.template_code == template_code)
            .order_by(ApprovalInstance.submitted_at.desc())
            .first()
        )

        if instance:
            return {
                "instance_id": instance.id,
                "instance_no": instance.instance_no,
                "status": instance.status,
                "submitted_at": instance.submitted_at.isoformat() if instance.submitted_at else None,
                "detail_url": f"/approval/instances/{instance.id}",
            }
        return None

    def _build_generic_bridge(
        self,
        project_id: int,
        from_stage: str,
        to_stage: str,
        missing_items: List[str],
    ) -> Dict[str, Any]:
        """构建通用特批入口（当没有精确匹配时的兜底）"""
        template_code = "PROJECT_STAGE_OVERRIDE"
        return {
            "approval_type": "STAGE_GATE_OVERRIDE",
            "approval_hint": f"阶段门校验未通过（{len(missing_items)}项未满足），可发起特批申请",
            "template_code": template_code,
            "template_exists": self._check_template_exists(template_code),
            "entity_type": "PROJECT",
            "urgency": "NORMAL",
            "action_url": self._build_action_url(
                template_code=template_code,
                entity_type="PROJECT",
                project_id=project_id,
                from_stage=from_stage,
                to_stage=to_stage,
            ),
            "form_data_prefill": {
                "project_id": project_id,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "gate_missing_items": missing_items,
                "override_reason": "",
            },
            "existing_instance": self._find_pending_instance(
                template_code=template_code,
                entity_type="PROJECT",
                entity_id=project_id,
            ),
        }
