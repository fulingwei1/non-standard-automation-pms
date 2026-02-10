# -*- coding: utf-8 -*-
"""
通用状态更新服务

提供统一的状态更新接口，支持：
- 状态值验证
- 状态转换规则验证
- 状态变更历史记录
- 关联实体状态联动
- 时间戳自动记录
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)


class StatusUpdateResult:
    """状态更新结果"""

    def __init__(
        self,
        success: bool,
        entity: Any = None,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        message: Optional[str] = None,
        errors: Optional[List[str]] = None,
    ):
        self.success = success
        self.entity = entity
        self.old_status = old_status
        self.new_status = new_status
        self.message = message
        self.errors = errors or []

    def __repr__(self):
        if self.success:
            return f"StatusUpdateResult(success=True, {self.old_status}→{self.new_status})"
        else:
            return f"StatusUpdateResult(success=False, errors={self.errors})"


class StatusUpdateService:
    """通用状态更新服务"""

    def __init__(self, db: Session):
        self.db = db

    def update_status(
        self,
        entity: Any,
        new_status: str,
        operator: User,
        *,
        valid_statuses: Optional[List[str]] = None,
        transition_rules: Optional[Dict[str, List[str]]] = None,
        status_field: str = "status",
        timestamp_fields: Optional[Dict[str, str]] = None,
        history_callback: Optional[Callable] = None,
        related_entities: Optional[List[Dict]] = None,
        reason: Optional[str] = None,
        before_update_callback: Optional[Callable] = None,
        after_update_callback: Optional[Callable] = None,
    ) -> StatusUpdateResult:
        """
        更新实体状态

        Args:
            entity: 要更新状态的实体对象
            new_status: 新状态值
            operator: 操作人
            valid_statuses: 有效状态列表（用于验证）
            transition_rules: 状态转换规则 {from_status: [to_status1, to_status2]}
            status_field: 状态字段名（默认"status"）
            timestamp_fields: 时间戳字段映射 {status_value: field_name}
            history_callback: 历史记录回调函数
            related_entities: 关联实体更新列表 [{"entity": obj, "field": "status", "value": "NEW_STATUS"}]
            reason: 状态变更原因
            before_update_callback: 更新前的回调函数
            after_update_callback: 更新后的回调函数

        Returns:
            StatusUpdateResult
        """
        errors = []

        # 1. 获取当前状态
        old_status = getattr(entity, status_field, None)

        # 2. 验证状态值
        if valid_statuses and new_status not in valid_statuses:
            errors.append(f"无效的状态值: {new_status}。有效状态: {', '.join(valid_statuses)}")
            return StatusUpdateResult(
                success=False,
                entity=entity,
                old_status=old_status,
                new_status=new_status,
                errors=errors,
            )

        # 3. 验证状态转换规则
        if transition_rules and old_status:
            # 如果当前状态在转换规则中，检查目标状态是否允许
            if old_status in transition_rules:
                allowed_statuses = transition_rules.get(old_status, [])
                if new_status not in allowed_statuses:
                    errors.append(
                        f"不允许的状态转换: {old_status} → {new_status}。"
                        f"允许的转换: {', '.join(allowed_statuses) if allowed_statuses else '无'}"
                    )
                    return StatusUpdateResult(
                        success=False,
                        entity=entity,
                        old_status=old_status,
                        new_status=new_status,
                        errors=errors,
                    )
            # 如果当前状态不在规则中，说明该状态不允许任何转换（包括到自己）
            else:
                errors.append(
                    f"状态 {old_status} 不允许转换到任何状态"
                )
                return StatusUpdateResult(
                    success=False,
                    entity=entity,
                    old_status=old_status,
                    new_status=new_status,
                    errors=errors,
                )

        # 4. 如果状态没有变化，直接返回
        if old_status == new_status:
            return StatusUpdateResult(
                success=True,
                entity=entity,
                old_status=old_status,
                new_status=new_status,
                message="状态未发生变化",
            )

        # 5. 执行更新前回调
        if before_update_callback:
            try:
                before_update_callback(entity, old_status, new_status, operator)
            except Exception as e:
                errors.append(f"更新前回调执行失败: {str(e)}")
                logger.error(f"before_update_callback failed: {e}", exc_info=True)
                return StatusUpdateResult(
                    success=False,
                    entity=entity,
                    old_status=old_status,
                    new_status=new_status,
                    errors=errors,
                )

        # 6. 更新状态
        setattr(entity, status_field, new_status)

        # 7. 更新时间戳字段
        if timestamp_fields:
            for status_value, field_name in timestamp_fields.items():
                if new_status == status_value:
                    if hasattr(entity, field_name):
                        current_value = getattr(entity, field_name, None)
                        if not current_value:  # 只在字段为空时设置
                            setattr(entity, field_name, datetime.now())
                    else:
                        logger.warning(
                            f"实体 {type(entity).__name__} 没有字段 {field_name}"
                        )

        # 8. 更新关联实体状态
        if related_entities:
            for related in related_entities:
                related_entity = related.get("entity")
                related_field = related.get("field", "status")
                related_value = related.get("value")
                if related_entity and related_value:
                    setattr(related_entity, related_field, related_value)
                    self.db.add(related_entity)

        # 9. 记录历史
        if history_callback:
            try:
                history_callback(
                    entity=entity,
                    old_status=old_status,
                    new_status=new_status,
                    operator=operator,
                    reason=reason,
                )
            except Exception as e:
                # 历史记录失败不影响主流程，但记录错误
                error_msg = f"历史记录失败: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg, exc_info=True)

        # 10. 提交数据库
        try:
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
        except Exception as e:
            self.db.rollback()
            errors.append(f"数据库提交失败: {str(e)}")
            logger.error(f"Database commit failed: {e}", exc_info=True)
            return StatusUpdateResult(
                success=False,
                entity=entity,
                old_status=old_status,
                new_status=new_status,
                errors=errors,
            )

        # 11. 执行更新后回调
        if after_update_callback:
            try:
                after_update_callback(entity, old_status, new_status, operator)
            except Exception as e:
                # 后回调失败不影响主流程，但记录错误
                error_msg = f"更新后回调执行失败: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg, exc_info=True)

        return StatusUpdateResult(
            success=True,
            entity=entity,
            old_status=old_status,
            new_status=new_status,
            message=f"状态已更新: {old_status} → {new_status}",
            errors=errors if errors else None,
        )

    def update_status_with_transition_log(
        self,
        entity: Any,
        new_status: str,
        operator: User,
        entity_type: str,
        *,
        valid_statuses: Optional[List[str]] = None,
        transition_rules: Optional[Dict[str, List[str]]] = None,
        status_field: str = "status",
        timestamp_fields: Optional[Dict[str, str]] = None,
        related_entities: Optional[List[Dict]] = None,
        reason: Optional[str] = None,
        action_type: Optional[str] = None,
        extra_data: Optional[Dict] = None,
        before_update_callback: Optional[Callable] = None,
        after_update_callback: Optional[Callable] = None,
    ) -> StatusUpdateResult:
        """
        更新状态并记录到统一的状态转换日志表

        Args:
            entity: 要更新状态的实体对象
            new_status: 新状态值
            operator: 操作人
            entity_type: 实体类型（用于日志记录）
            其他参数同 update_status

        Returns:
            StatusUpdateResult
        """
        # 获取实体ID
        entity_id = getattr(entity, "id", None)
        if not entity_id:
            return StatusUpdateResult(
                success=False,
                entity=entity,
                errors=["实体没有id字段"],
            )

        # 创建历史记录回调
        def history_callback(inner_entity, old_status, new_status, operator, reason):
            try:
                from app.models.state_machine import StateTransitionLog

                log = StateTransitionLog(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    from_state=old_status or "",
                    to_state=new_status,
                    operator_id=operator.id,
                    operator_name=operator.real_name or operator.username,
                    action_type=action_type,
                    comment=reason,
                    extra_data=extra_data,
                )
                self.db.add(log)
            except ImportError:
                logger.warning("StateTransitionLog model not found, skipping log")
            except Exception as e:
                logger.error(f"Failed to create state transition log: {e}", exc_info=True)
                raise

        return self.update_status(
            entity=entity,
            new_status=new_status,
            operator=operator,
            valid_statuses=valid_statuses,
            transition_rules=transition_rules,
            status_field=status_field,
            timestamp_fields=timestamp_fields,
            history_callback=history_callback,
            related_entities=related_entities,
            reason=reason,
            before_update_callback=before_update_callback,
            after_update_callback=after_update_callback,
        )
