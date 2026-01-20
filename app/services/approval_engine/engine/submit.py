# -*- coding: utf-8 -*-
"""
审批发起功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTemplate
from app.models.user import User

from .core import ApprovalEngineCore


class ApprovalSubmitMixin:
    """审批发起功能混入类"""

    def submit(
        self: ApprovalEngineCore,
        template_code: str,
        entity_type: str,
        entity_id: int,
        form_data: Dict[str, Any],
        initiator_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        urgency: str = "NORMAL",
        cc_user_ids: Optional[List[int]] = None,
    ) -> ApprovalInstance:
        """
        提交审批

        Args:
            template_code: 审批模板编码
            entity_type: 业务实体类型（如QUOTE/CONTRACT/ECN）
            entity_id: 业务实体ID
            form_data: 表单数据
            initiator_id: 发起人ID
            title: 审批标题
            summary: 审批摘要
            urgency: 紧急程度（NORMAL/URGENT/CRITICAL）
            cc_user_ids: 抄送人ID列表

        Returns:
            创建的审批实例
        """
        # 1. 获取模板
        template = (
            self.db.query(ApprovalTemplate)
            .filter(
                ApprovalTemplate.template_code == template_code,
                ApprovalTemplate.is_active == True,
            )
            .first()
        )

        if not template:
            raise ValueError(f"审批模板不存在: {template_code}")

        # 2. 获取发起人信息
        initiator = self.db.query(User).filter(User.id == initiator_id).first()
        if not initiator:
            raise ValueError(f"发起人不存在: {initiator_id}")

        # 3. 构建上下文
        context = {
            "form_data": form_data,
            "initiator": {
                "id": initiator.id,
                "name": initiator.name,
                "dept_id": initiator.department_id,
            },
            "entity": {"type": entity_type, "id": entity_id},
        }

        # 4. 选择审批流程
        flow = self.router.select_flow(template.id, context)
        if not flow:
            raise ValueError(f"未找到适用的审批流程: {template_code}")

        # 5. 创建审批实例
        instance_no = self._generate_instance_no(template_code)
        instance = ApprovalInstance(
            instance_no=instance_no,
            template_id=template.id,
            flow_id=flow.id,
            entity_type=entity_type,
            entity_id=entity_id,
            initiator_id=initiator_id,
            initiator_name=initiator.name,
            initiator_dept_id=initiator.department_id,
            form_data=form_data,
            status="PENDING",
            urgency=urgency,
            title=title or f"{template.template_name} - {initiator.name}",
            summary=summary,
            submitted_at=datetime.now(),
        )
        self.db.add(instance)
        self.db.flush()

        # 6. 记录操作日志
        self._log_action(
            instance_id=instance.id,
            operator_id=initiator_id,
            operator_name=initiator.name,
            action="SUBMIT",
            comment=None,
        )

        # 7. 创建第一个节点的任务
        first_node = self._get_first_node(flow.id)
        if first_node:
            instance.current_node_id = first_node.id
            self._create_node_tasks(instance, first_node, context)

        # 8. 处理抄送
        if cc_user_ids:
            self.executor.create_cc_records(
                instance=instance,
                node_id=None,
                cc_user_ids=cc_user_ids,
                cc_source="INITIATOR",
                added_by=initiator_id,
            )

        self.db.commit()
        return instance

    def save_draft(
        self: ApprovalEngineCore,
        template_code: str,
        entity_type: str,
        entity_id: int,
        form_data: Dict[str, Any],
        initiator_id: int,
        title: Optional[str] = None,
    ) -> ApprovalInstance:
        """保存审批草稿"""
        template = (
            self.db.query(ApprovalTemplate)
            .filter(
                ApprovalTemplate.template_code == template_code,
                ApprovalTemplate.is_active == True,
            )
            .first()
        )

        if not template:
            raise ValueError(f"审批模板不存在: {template_code}")

        initiator = self.db.query(User).filter(User.id == initiator_id).first()

        instance = ApprovalInstance(
            instance_no=self._generate_instance_no(template_code),
            template_id=template.id,
            entity_type=entity_type,
            entity_id=entity_id,
            initiator_id=initiator_id,
            initiator_name=initiator.name if initiator else None,
            form_data=form_data,
            status="DRAFT",
            title=title,
        )
        self.db.add(instance)
        self.db.commit()

        return instance
