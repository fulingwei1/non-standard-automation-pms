# -*- coding: utf-8 -*-
"""
状态机通知服务

提供统一的状态转换通知机制，支持：
- 灵活的接收人解析（创建人、负责人、审批人等）
- 通知模板系统
- 与统一通知服务集成
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.unified_notification_service import get_notification_service
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class StateMachineNotifier:
    """
    状态机通知服务

    提供声明式的状态转换通知功能：
    1. 解析接收人（支持creator、assignee、approvers等用户类型）
    2. 构建通知内容（支持模板系统）
    3. 调用统一通知服务发送通知

    使用方式：
        notifier = StateMachineNotifier()
        notifier.send_transition_notification(
            db=db,
            entity=issue,
            entity_type="ISSUE",
            from_state="OPEN",
            to_state="IN_PROGRESS",
            operator=current_user,
            notify_users=["assignee", "reporter"],
            template="issue_status_changed"
        )
    """

    def __init__(self):
        self.notification_service = None  # Lazy init with db session

    def resolve_notification_recipients(
        self,
        entity: Any,
        notify_user_types: List[str],
    ) -> List[int]:
        """
        解析通知接收人列表

        Args:
            entity: 业务实体对象（Issue、ECN、Project等）
            notify_user_types: 用户类型列表，支持：
                - "creator" / "created_by": 实体创建人
                - "assignee": 当前负责人
                - "reporter": 问题报告人
                - "approvers": 审批人列表
                - "project_manager": 关联项目经理
                - "team_members": 团队成员列表

        Returns:
            用户ID列表（去重）
        """
        recipient_ids = set()

        for user_type in notify_user_types:
            try:
                if user_type in ["creator", "created_by"]:
                    # 方式1: created_by_id 字段
                    if hasattr(entity, 'created_by_id') and entity.created_by_id:
                        recipient_ids.add(entity.created_by_id)
                    # 方式2: creator_id 字段
                    elif hasattr(entity, 'creator_id') and entity.creator_id:
                        recipient_ids.add(entity.creator_id)
                    # 方式3: created_by 关系
                    elif hasattr(entity, 'created_by') and entity.created_by:
                        recipient_ids.add(entity.created_by.id)

                elif user_type == "assignee":
                    # 方式1: assignee_id 字段
                    if hasattr(entity, 'assignee_id') and entity.assignee_id:
                        recipient_ids.add(entity.assignee_id)
                    # 方式2: assigned_to_id 字段
                    elif hasattr(entity, 'assigned_to_id') and entity.assigned_to_id:
                        recipient_ids.add(entity.assigned_to_id)
                    # 方式3: assignee 关系
                    elif hasattr(entity, 'assignee') and entity.assignee:
                        recipient_ids.add(entity.assignee.id)

                elif user_type == "reporter":
                    # Issue模块的报告人
                    if hasattr(entity, 'reporter_id') and entity.reporter_id:
                        recipient_ids.add(entity.reporter_id)
                    elif hasattr(entity, 'reporter') and entity.reporter:
                        recipient_ids.add(entity.reporter.id)

                elif user_type == "approvers":
                    # 获取审批人列表
                    if hasattr(entity, 'approvers') and entity.approvers:
                        for approver in entity.approvers:
                            if hasattr(approver, 'id'):
                                recipient_ids.add(approver.id)
                            elif isinstance(approver, int):
                                recipient_ids.add(approver)
                    # 或者从approver_ids字段
                    elif hasattr(entity, 'approver_ids') and entity.approver_ids:
                        if isinstance(entity.approver_ids, list):
                            recipient_ids.update(entity.approver_ids)

                elif user_type == "project_manager":
                    # 关联项目的经理
                    if hasattr(entity, 'project') and entity.project:
                        if hasattr(entity.project, 'manager_id') and entity.project.manager_id:
                            recipient_ids.add(entity.project.manager_id)
                        elif hasattr(entity.project, 'manager') and entity.project.manager:
                            recipient_ids.add(entity.project.manager.id)

                elif user_type == "team_members":
                    # 团队成员列表
                    if hasattr(entity, 'team_members') and entity.team_members:
                        for member in entity.team_members:
                            if hasattr(member, 'user_id'):
                                recipient_ids.add(member.user_id)
                            elif hasattr(member, 'id'):
                                recipient_ids.add(member.id)

            except Exception as e:
                logger.warning(f"解析接收人 '{user_type}' 失败: {e}")
                continue

        return list(recipient_ids)

    def build_notification_content(
        self,
        entity_type: str,
        entity: Any,
        from_state: str,
        to_state: str,
        operator: Optional[Any] = None,
        template: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        构建通知标题和内容

        Args:
            entity_type: 实体类型（ISSUE、ECN、PROJECT等）
            entity: 业务实体对象
            from_state: 源状态
            to_state: 目标状态
            operator: 操作人
            template: 通知模板名称（可选）

        Returns:
            (title, content) 元组
        """
        # 获取实体描述信息
        entity_name = self._get_entity_name(entity)
        operator_name = self._get_operator_name(operator)

        # 如果指定了模板，使用模板系统（未来扩展）
        if template:
            return self._build_from_template(
                template, entity_type, entity_name, from_state, to_state, operator_name
            )

        # 默认通知内容
        title = f"{entity_type}状态变更通知"

        content = f"{entity_type}: {entity_name}\n"
        content += f"状态变更: {from_state} → {to_state}\n"

        if operator_name:
            content += f"操作人: {operator_name}\n"

        return title, content

    def _get_entity_name(self, entity: Any) -> str:
        """获取实体名称"""
        # 尝试多种命名字段
        for attr in ['title', 'name', 'code', 'number', 'id']:
            if hasattr(entity, attr):
                value = getattr(entity, attr)
                if value:
                    return str(value)
        return "未知"

    def _get_operator_name(self, operator: Optional[Any]) -> Optional[str]:
        """获取操作人姓名"""
        if not operator:
            return None

        # 尝试多种姓名字段
        for attr in ['name', 'username', 'nickname', 'real_name']:
            if hasattr(operator, attr):
                value = getattr(operator, attr)
                if value:
                    return str(value)

        return None

    def _build_from_template(
        self,
        template: str,
        entity_type: str,
        entity_name: str,
        from_state: str,
        to_state: str,
        operator_name: Optional[str],
    ) -> tuple[str, str]:
        """
        从模板构建通知内容（预留接口）

        未来可以扩展为：
        1. 从数据库加载模板
        2. 支持变量替换（如 {entity_name}、{to_state}）
        3. 支持多语言
        """
        # 目前使用简单的映射
        templates = {
            "issue_status_changed": (
                "问题状态变更",
                f"问题 {entity_name} 的状态已从 {from_state} 变更为 {to_state}",
            ),
            "ecn_submitted": (
                "ECN已提交审批",
                f"工程变更 {entity_name} 已提交，请及时审批",
            ),
            "ecn_approved": (
                "ECN审批通过",
                f"工程变更 {entity_name} 已审批通过，请查看执行计划",
            ),
            "project_stage_changed": (
                "项目阶段变更",
                f"项目 {entity_name} 进入 {to_state} 阶段",
            ),
        }

        if template in templates:
            return templates[template]

        # 回退到默认格式
        return (
            f"{entity_type}通知",
            f"{entity_name}: {from_state} → {to_state}",
        )

    def send_transition_notification(
        self,
        db: Session,
        entity: Any,
        entity_type: str,
        entity_id: int,
        from_state: str,
        to_state: str,
        operator: Optional[Any] = None,
        notify_user_types: Optional[List[str]] = None,
        template: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        发送状态转换通知

        Args:
            db: 数据库会话
            entity: 业务实体对象
            entity_type: 实体类型（ISSUE、ECN、PROJECT等）
            entity_id: 实体ID
            from_state: 源状态
            to_state: 目标状态
            operator: 操作人（可选）
            notify_user_types: 通知用户类型列表（可选）
            template: 通知模板名称（可选）
            priority: 通知优先级（默认NORMAL）
            extra_data: 额外数据（可选）

        Returns:
            是否发送成功
        """
        if not notify_user_types:
            # 如果没有指定接收人，不发送通知
            return True

        try:
            # 1. 解析接收人
            recipient_ids = self.resolve_notification_recipients(entity, notify_user_types)

            if not recipient_ids:
                logger.warning(
                    f"状态转换通知：未找到接收人 (entity_type={entity_type}, "
                    f"entity_id={entity_id}, notify_types={notify_user_types})"
                )
                return False

            # 2. 构建通知内容
            title, content = self.build_notification_content(
                entity_type, entity, from_state, to_state, operator, template
            )

            # 3. 构建跳转链接
            link = self._build_entity_link(entity_type, entity_id)

            # 4. 准备额外数据
            notification_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "from_state": from_state,
                "to_state": to_state,
            }
            if extra_data:
                notification_data.update(extra_data)

            # 5. 发送通知给每个接收人（使用统一通知服务）
            unified_service = get_notification_service(db)
            success = True
            for recipient_id in recipient_ids:
                try:
                    request = NotificationRequest(
                        recipient_id=recipient_id,
                        notification_type="STATE_TRANSITION",
                        category=entity_type.lower() if entity_type else "general",
                        title=title,
                        content=content,
                        priority=priority or NotificationPriority.NORMAL,
                        source_type=entity_type.lower() if entity_type else None,
                        source_id=entity_id,
                        link_url=link,
                        extra_data=notification_data,
                    )
                    unified_service.send_notification(request)
                except Exception as e:
                    logger.error(f"发送通知给用户 {recipient_id} 失败: {e}")
                    success = False

            return success

        except Exception as e:
            logger.error(f"发送状态转换通知失败: {e}")
            return False

    def _build_entity_link(self, entity_type: str, entity_id: int) -> str:
        """
        构建实体跳转链接

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            跳转链接URL
        """
        # 根据实体类型构建前端路由
        entity_routes = {
            "ISSUE": f"/issues/{entity_id}",
            "ECN": f"/ecn/{entity_id}",
            "PROJECT": f"/projects/{entity_id}",
            "TASK": f"/tasks/{entity_id}",
            "APPROVAL": f"/approvals/{entity_id}",
        }

        return entity_routes.get(entity_type, f"/{entity_type.lower()}/{entity_id}")
