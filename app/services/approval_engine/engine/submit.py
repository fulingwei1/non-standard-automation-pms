# -*- coding: utf-8 -*-
"""
审批发起功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.approval import ApprovalInstance, ApprovalTemplate
from app.models.user import User

from ..adapters import get_adapter
from .core import ApprovalEngineCore


class ApprovalSubmitMixin:
    """审批发起功能混入类"""

    def __init__(self, db=None):
        """允许独立实例化（兼容测试）"""
        if db is not None:
            self.db = db

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
                ApprovalTemplate.is_active,
            )
            .first()
        )

        if not template:
            raise ValueError(f"审批模板不存在: {template_code}")

        # 2. 获取发起人信息
        initiator = self.db.query(User).filter(User.id == initiator_id).first()
        if not initiator:
            raise ValueError(f"发起人不存在: {initiator_id}")

        # 3. 获取业务适配器并验证
        adapter = None
        try:
            adapter = get_adapter(entity_type, self.db)
            # 验证是否可以提交
            can_submit, error_msg = adapter.validate_submit(entity_id)
            if not can_submit:
                raise ValueError(error_msg)
        except ValueError as e:
            # 如果适配器不存在或验证失败，抛出异常
            if "不支持的业务类型" not in str(e):
                raise
            # 对于未配置适配器的业务类型，允许继续（保持向后兼容）

        # 4. 构建上下文（合并表单数据和实体数据）
        context = {
            "form_data": form_data,
            "initiator": {
                "id": initiator.id,
                "name": initiator.real_name or initiator.username,
                "dept_id": None,  # User model uses department string, not ID
            },
            "entity": {"type": entity_type, "id": entity_id},
        }

        # 如果有适配器，获取实体数据用于条件路由
        if adapter:
            entity_data = adapter.get_entity_data(entity_id)
            context["entity_data"] = entity_data
            # 合并到form_data供条件路由使用
            context["form_data"] = {**form_data, "entity": entity_data}

        # 5. 选择审批流程
        flow = self.router.select_flow(template.id, context)
        if not flow:
            raise ValueError(f"未找到适用的审批流程: {template_code}")

        # 6. 确定标题和摘要
        if adapter:
            if not title and hasattr(adapter, "generate_title"):
                title = adapter.generate_title(entity_id)
            if not summary and hasattr(adapter, "generate_summary"):
                summary = adapter.generate_summary(entity_id)

        # 7. 创建审批实例
        instance_no = self._generate_instance_no(template_code)
        instance = ApprovalInstance(
            instance_no=instance_no,
            template_id=template.id,
            flow_id=flow.id,
            entity_type=entity_type,
            entity_id=entity_id,
            initiator_id=initiator_id,
            initiator_name=initiator.real_name or initiator.username,
            initiator_dept_id=None,
            form_data=form_data,
            status="PENDING",
            urgency=urgency,
            title=title
            or f"{template.template_name} - {initiator.real_name or initiator.username}",
            summary=summary,
            submitted_at=datetime.now(),
        )
        self.db.add(instance)
        self.db.flush()

        # 8. 调用适配器的提交回调
        if adapter:
            adapter.on_submit(entity_id, instance)

        # 9. 记录操作日志
        self._log_action(
            instance_id=instance.id,
            operator_id=initiator_id,
            operator_name=initiator.real_name or initiator.username,
            action="SUBMIT",
            comment=None,
        )

        # 10. 创建第一个节点的任务
        first_node = self._get_first_node(flow.id)
        if first_node:
            instance.current_node_id = first_node.id
            self._create_node_tasks(instance, first_node, context)

        # 11. 处理抄送
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
                ApprovalTemplate.is_active,
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
            initiator_name=initiator.real_name or initiator.username
            if initiator
            else None,
            form_data=form_data,
            status="DRAFT",
            title=title,
        )
        self.db.add(instance)
        self.db.commit()

        return instance
