# -*- coding: utf-8 -*-
"""
预警规则引擎

提供统一的预警规则评估框架，支持：
1. 规则条件评估
2. 预警记录创建
3. 预警去重和升级
4. 级别动态提升
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.alert import (
    AlertRule, AlertRecord, AlertNotification
)
from app.models.enums import (
    AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum
)
from app.services.notification_service import AlertNotificationService
from app.services.alert_subscription_service import AlertSubscriptionService


class AlertRuleEngine:
    """预警规则引擎基类"""
    
    # 预警级别优先级（用于比较）
    LEVEL_PRIORITY = {
        AlertLevelEnum.INFO.value: 1,
        AlertLevelEnum.WARNING.value: 2,
        AlertLevelEnum.CRITICAL.value: 3,
        AlertLevelEnum.URGENT.value: 4,
    }
    
    # 响应时限（小时）
    RESPONSE_TIMEOUT = {
        AlertLevelEnum.INFO.value: 24,
        AlertLevelEnum.WARNING.value: 8,
        AlertLevelEnum.CRITICAL.value: 4,
        AlertLevelEnum.URGENT.value: 1,
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = AlertNotificationService(db)
        self.subscription_service = AlertSubscriptionService(db)
    
    def evaluate_rule(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[AlertRecord]:
        """
        评估规则并创建预警记录（如果条件满足）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据，必须包含：
                - target_type: 对象类型
                - target_id: 对象ID
                - target_no: 对象编号（可选）
                - target_name: 对象名称（可选）
                - project_id: 项目ID（可选）
                - machine_id: 设备ID（可选）
            context: 上下文数据（可选）
        
        Returns:
            AlertRecord: 创建的预警记录，如果未创建则返回 None
        """
        if not rule.is_enabled:
            return None
        
        # 检查触发条件
        if not self.check_condition(rule, target_data, context):
            return None
        
        # 确定预警级别
        alert_level = self.determine_alert_level(rule, target_data, context)
        
        # 检查是否应该创建预警（去重逻辑）
        existing_alert = self.should_create_alert(rule, target_data, alert_level)
        
        if existing_alert:
            # 如果已有预警且级别更高，升级现有预警
            if self.level_priority(alert_level) > self.level_priority(existing_alert.alert_level):
                return self.upgrade_alert(existing_alert, alert_level, target_data, context)
            # 如果级别相同或更低，不重复创建
            return None
        
        # 创建新的预警记录
        return self.create_alert(rule, target_data, alert_level, context)
    
    def check_condition(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        检查规则触发条件是否满足（子类可重写）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            bool: 是否满足触发条件
        """
        if rule.condition_type == 'THRESHOLD':
            return self.match_threshold(rule, target_data, context)
        elif rule.condition_type == 'DEVIATION':
            return self.match_deviation(rule, target_data, context)
        elif rule.condition_type == 'OVERDUE':
            return self.match_overdue(rule, target_data, context)
        elif rule.condition_type == 'CUSTOM':
            return self.match_custom_expr(rule, target_data, context)
        else:
            return False
    
    def match_threshold(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        阈值匹配
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            bool: 是否匹配
        """
        if not rule.target_field:
            return False
        
        # 获取字段值
        field_value = self.get_field_value(rule.target_field, target_data, context)
        if field_value is None:
            return False
        
        try:
            field_value = float(field_value)
        except (ValueError, TypeError):
            return False
        
        operator = rule.condition_operator or 'GT'
        
        if operator == 'BETWEEN':
            if not rule.threshold_min or not rule.threshold_max:
                return False
            try:
                min_val = float(rule.threshold_min)
                max_val = float(rule.threshold_max)
                return min_val <= field_value <= max_val
            except (ValueError, TypeError):
                return False
        elif operator == 'GT':
            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            return field_value > threshold
        elif operator == 'GTE':
            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            return field_value >= threshold
        elif operator == 'LT':
            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            return field_value < threshold
        elif operator == 'LTE':
            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            return field_value <= threshold
        elif operator == 'EQ':
            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            return abs(field_value - threshold) < 0.0001  # 浮点数比较
        else:
            return False
    
    def match_deviation(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        偏差匹配（实际值与计划值的偏差）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            bool: 是否匹配
        """
        # 需要实际值和计划值
        actual_field = rule.target_field or 'actual_value'
        planned_field = rule.target_field.replace('actual', 'planned') if rule.target_field else 'planned_value'
        
        actual_value = self.get_field_value(actual_field, target_data, context)
        planned_value = self.get_field_value(planned_field, target_data, context)
        
        if actual_value is None or planned_value is None:
            return False
        
        try:
            actual_value = float(actual_value)
            planned_value = float(planned_value)
            deviation = actual_value - planned_value
            
            threshold = float(rule.threshold_value) if rule.threshold_value else 0
            operator = rule.condition_operator or 'GT'
            
            if operator == 'GT':
                return deviation > threshold
            elif operator == 'GTE':
                return deviation >= threshold
            elif operator == 'LT':
                return deviation < threshold
            elif operator == 'LTE':
                return deviation <= threshold
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def match_overdue(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        逾期匹配
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            bool: 是否匹配
        """
        # 需要截止日期字段
        due_date_field = rule.target_field or 'due_date'
        due_date = self.get_field_value(due_date_field, target_data, context)
        
        if not due_date:
            return False
        
        if isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return False
        
        if isinstance(due_date, datetime):
            now = datetime.now()
            if due_date.tzinfo:
                now = now.replace(tzinfo=due_date.tzinfo)
            
            advance_days = rule.advance_days or 0
            check_date = due_date - timedelta(days=advance_days)
            
            return now >= check_date
        else:
            return False
    
    def match_custom_expr(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        自定义表达式匹配（简单实现，实际可以使用更复杂的表达式引擎）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            bool: 是否匹配
        """
        if not rule.condition_expr:
            return False
        
        # 简单的表达式评估（实际应该使用安全的表达式引擎）
        # 这里仅做示例，实际使用时需要更安全的实现
        try:
            # 构建评估上下文
            eval_context = {}
            eval_context.update(target_data)
            if context:
                eval_context.update(context)
            
            # TODO: 实现安全的表达式引擎（如 simpleeval）替代 eval
            # 暂时返回 False，需要实现安全的表达式引擎
            return False
        except Exception:
            return False
    
    def get_field_value(
        self,
        field_path: str,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        获取字段值（支持点号分隔的嵌套路径）
        
        Args:
            field_path: 字段路径，如 'project.progress' 或 'days_delay'
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            字段值
        """
        # 先在 target_data 中查找
        value = self._get_nested_value(field_path, target_data)
        if value is not None:
            return value
        
        # 再在 context 中查找
        if context:
            value = self._get_nested_value(field_path, context)
            if value is not None:
                return value
        
        return None
    
    def _get_nested_value(self, field_path: str, data: Dict[str, Any]) -> Any:
        """获取嵌套字段值"""
        parts = field_path.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
            if value is None:
                return None
        return value
    
    def determine_alert_level(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        确定预警级别（子类可重写以实现更复杂的级别判断）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            str: 预警级别
        """
        # 默认使用规则配置的级别
        return rule.alert_level or AlertLevelEnum.WARNING.value
    
    def should_create_alert(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str
    ) -> Optional[AlertRecord]:
        """
        检查是否应该创建预警（去重逻辑）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别
        
        Returns:
            AlertRecord: 如果存在相同来源的活跃预警，返回该预警；否则返回 None
        """
        target_type = target_data.get('target_type')
        target_id = target_data.get('target_id')
        
        if not target_type or not target_id:
            return None
        
        # 查询相同来源的活跃预警（24小时内）
        time_window = datetime.now() - timedelta(hours=24)
        
        existing_alert = self.db.query(AlertRecord).filter(
            AlertRecord.rule_id == rule.id,
            AlertRecord.target_type == target_type,
            AlertRecord.target_id == target_id,
            AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED']),
            AlertRecord.created_at >= time_window
        ).order_by(AlertRecord.created_at.desc()).first()
        
        return existing_alert
    
    def upgrade_alert(
        self,
        alert: AlertRecord,
        new_level: str,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AlertRecord:
        """
        升级预警级别
        
        Args:
            alert: 现有预警记录
            new_level: 新的预警级别
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            AlertRecord: 升级后的预警记录
        """
        old_level = alert.alert_level
        
        # 更新预警级别
        alert.alert_level = new_level
        alert.is_escalated = True
        alert.escalated_at = datetime.now()
        
        # 更新预警内容
        alert.alert_title = self.generate_alert_title(alert.rule, target_data, new_level, context)
        alert.alert_content = self.generate_alert_content(alert.rule, target_data, new_level, context)
        
        # 更新触发值
        if rule := alert.rule:
            if rule.target_field:
                trigger_value = self.get_field_value(rule.target_field, target_data, context)
                if trigger_value is not None:
                    alert.trigger_value = str(trigger_value)
        
        self.db.add(alert)
        self.db.flush()
        
        # 创建升级记录（使用 AlertRecord 的 is_escalated 字段记录升级状态）
        # ExceptionEscalation 模型主要用于异常事件，预警升级通过 AlertRecord 字段记录
        # 如果需要详细记录，可以创建专门的 AlertEscalation 表，这里暂时使用现有字段
        
        # 发送升级通知（使用订阅匹配）
        try:
            # 获取通知接收人（基于订阅配置）
            recipients = self.subscription_service.get_notification_recipients(alert, alert.rule)
            
            if recipients['user_ids']:
                # 有匹配的订阅，发送通知（升级通知强制发送）
                self.notification_service.send_alert_notification(
                    alert=alert,
                    user_ids=recipients['user_ids'],
                    channels=recipients['channels'],
                    force_send=True  # 升级通知强制发送，忽略免打扰时段
                )
            else:
                # 没有匹配的订阅，使用规则默认配置
                self.notification_service.send_alert_notification(
                    alert=alert,
                    force_send=True
                )
        except Exception as e:
            # 通知发送失败不影响升级操作
            import logging
            logging.getLogger(__name__).error(f"升级通知发送失败: {e}")
        
        return alert
    
    def create_alert(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AlertRecord:
        """
        创建预警记录
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别
            context: 上下文数据
        
        Returns:
            AlertRecord: 创建的预警记录
        """
        # 生成预警编号
        alert_no = self.generate_alert_no(rule, target_data)
        
        # 获取触发值
        trigger_value = None
        if rule.target_field:
            trigger_value = self.get_field_value(rule.target_field, target_data, context)
        
        # 创建预警记录
        alert = AlertRecord(
            alert_no=alert_no,
            rule_id=rule.id,
            target_type=target_data.get('target_type'),
            target_id=target_data.get('target_id'),
            target_no=target_data.get('target_no'),
            target_name=target_data.get('target_name'),
            project_id=target_data.get('project_id'),
            machine_id=target_data.get('machine_id'),
            alert_level=alert_level,
            alert_title=self.generate_alert_title(rule, target_data, alert_level, context),
            alert_content=self.generate_alert_content(rule, target_data, alert_level, context),
            alert_data=target_data,
            status=AlertStatusEnum.PENDING.value,
            triggered_at=datetime.now(),
            trigger_value=str(trigger_value) if trigger_value is not None else None,
            threshold_value=rule.threshold_value
        )
        
        self.db.add(alert)
        self.db.flush()
        
        # 发送通知（使用订阅匹配）
        try:
            # 获取通知接收人（基于订阅配置）
            recipients = self.subscription_service.get_notification_recipients(alert, rule)
            
            if recipients['user_ids']:
                # 有匹配的订阅，发送通知
                self.notification_service.send_alert_notification(
                    alert=alert,
                    user_ids=recipients['user_ids'],
                    channels=recipients['channels']
                )
            else:
                # 没有匹配的订阅，使用规则默认配置
                self.notification_service.send_alert_notification(alert=alert)
        except Exception as e:
            # 通知发送失败不影响预警创建
            import logging
            logging.getLogger(__name__).error(f"预警通知发送失败: {e}")
        
        return alert
    
    def generate_alert_no(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any]
    ) -> str:
        """
        生成预警编号
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
        
        Returns:
            str: 预警编号
        """
        today = datetime.now().strftime('%Y%m%d')
        rule_code = rule.rule_code[:3].upper()
        
        # 查询今天的预警数量
        count = self.db.query(AlertRecord).filter(
            AlertRecord.alert_no.like(f'{rule_code}{today}%')
        ).count()
        
        return f'{rule_code}{today}{str(count + 1).zfill(4)}'
    
    def generate_alert_title(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成预警标题（子类可重写）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别
            context: 上下文数据
        
        Returns:
            str: 预警标题
        """
        target_name = target_data.get('target_name') or target_data.get('target_no') or '对象'
        return f'{rule.rule_name}：{target_name}'
    
    def generate_alert_content(
        self,
        rule: AlertRule,
        target_data: Dict[str, Any],
        alert_level: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成预警内容（子类可重写）
        
        Args:
            rule: 预警规则
            target_data: 目标对象数据
            alert_level: 预警级别
            context: 上下文数据
        
        Returns:
            str: 预警内容
        """
        content = f'{rule.rule_name}\n'
        if rule.description:
            content += f'说明：{rule.description}\n'
        
        if rule.target_field:
            trigger_value = self.get_field_value(rule.target_field, target_data, context)
            if trigger_value is not None:
                content += f'当前值：{trigger_value}\n'
        
        if rule.threshold_value:
            content += f'阈值：{rule.threshold_value}\n'
        
        if rule.solution_guide:
            content += f'\n处理建议：{rule.solution_guide}'
        
        return content
    
    def level_priority(self, level: str) -> int:
        """
        获取预警级别优先级
        
        Args:
            level: 预警级别
        
        Returns:
            int: 优先级（数字越大优先级越高）
        """
        return self.LEVEL_PRIORITY.get(level, 0)
    
    def check_level_escalation(
        self,
        alert: AlertRecord,
        target_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[AlertRecord]:
        """
        检查预警级别是否需要动态提升
        
        Args:
            alert: 现有预警记录
            target_data: 目标对象数据
            context: 上下文数据
        
        Returns:
            AlertRecord: 如果级别提升，返回更新后的预警；否则返回 None
        """
        if not alert.rule:
            return None
        
        # 检查是否在24小时内已升级过
        if alert.is_escalated and alert.escalated_at:
            time_since_escalation = datetime.now() - alert.escalated_at
            if time_since_escalation < timedelta(hours=24):
                return None
        
        # 重新评估条件，确定新的预警级别
        new_level = self.determine_alert_level(alert.rule, target_data, context)
        
        # 如果新级别更高，则升级
        if self.level_priority(new_level) > self.level_priority(alert.alert_level):
            return self.upgrade_alert(alert, new_level, target_data, context)
        
        return None
    
    @staticmethod
    def get_or_create_rule(
        db: Session,
        rule_code: str,
        default_config: Dict[str, Any]
    ) -> AlertRule:
        """
        获取或创建预警规则
        
        Args:
            db: 数据库会话
            rule_code: 规则编码
            default_config: 默认配置
        
        Returns:
            AlertRule: 预警规则
        """
        rule = db.query(AlertRule).filter(
            AlertRule.rule_code == rule_code
        ).first()
        
        if not rule:
            rule = AlertRule(
                rule_code=rule_code,
                is_system=True,
                is_enabled=True,
                **default_config
            )
            db.add(rule)
            db.flush()
        
        return rule
