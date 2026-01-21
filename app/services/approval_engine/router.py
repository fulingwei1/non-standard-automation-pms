# -*- coding: utf-8 -*-
"""
审批路由决策服务

根据表单数据和上下文信息，选择适用的审批流程和节点
支持复杂条件表达式的评估
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalNodeDefinition,
    ApprovalRoutingRule,
)


class ApprovalRouterService:
    """审批路由决策服务"""

    def __init__(self, db: Session):
        self.db = db

    def select_flow(
        self,
        template_id: int,
        context: Dict[str, Any],
    ) -> Optional[ApprovalFlowDefinition]:
        """
        根据上下文选择适用的审批流程

        Args:
            template_id: 审批模板ID
            context: 上下文数据，包含：
                - form_data: 表单数据
                - initiator: 发起人信息
                - entity: 业务实体数据（通过适配器获取）

        Returns:
            匹配的审批流程定义，如无匹配则返回默认流程
        """
        # 获取该模板的所有路由规则，按优先级排序
        rules = (
            self.db.query(ApprovalRoutingRule)
            .filter(
                ApprovalRoutingRule.template_id == template_id,
                ApprovalRoutingRule.is_active == True,
            )
            .order_by(ApprovalRoutingRule.rule_order)
            .all()
        )

        # 依次匹配规则
        for rule in rules:
            if rule.conditions and self._evaluate_conditions(rule.conditions, context):
                return rule.flow

        # 没有匹配的规则，使用默认流程
        return self._get_default_flow(template_id)

    def _get_default_flow(self, template_id: int) -> Optional[ApprovalFlowDefinition]:
        """获取模板的默认流程"""
        return (
            self.db.query(ApprovalFlowDefinition)
            .filter(
                ApprovalFlowDefinition.template_id == template_id,
                ApprovalFlowDefinition.is_default == True,
                ApprovalFlowDefinition.is_active == True,
            )
            .first()
        )

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        评估条件表达式

        条件格式示例：
        {
            "operator": "AND",  // AND/OR
            "items": [
                {"field": "form.leave_days", "op": "<=", "value": 3},
                {"field": "entity.gross_margin", "op": ">=", "value": 0.2}
            ]
        }
        """
        operator = conditions.get("operator", "AND")
        items = conditions.get("items", [])

        if not items:
            return True

        results = [self._evaluate_single(item, context) for item in items]

        if operator == "AND":
            return all(results)
        else:  # OR
            return any(results)

    def _evaluate_single(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """评估单个条件"""
        field = condition.get("field", "")
        op = condition.get("op", "==")
        expected = condition.get("value")

        # 获取字段值
        actual = self._get_field_value(field, context)

        # 比较
        return self._compare(actual, op, expected)

    def _get_field_value(self, field_path: str, context: Dict[str, Any]) -> Any:
        """
        获取字段值，支持嵌套路径

        支持的路径前缀：
        - form.xxx: 表单字段
        - entity.xxx: 业务实体属性
        - initiator.xxx: 发起人属性
        - sys.xxx: 系统变量
        """
        if not field_path:
            return None

        parts = field_path.split(".")
        value = context

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

    def _compare(self, actual: Any, op: str, expected: Any) -> bool:
        """
        比较操作

        支持的操作符：
        - ==, !=: 相等/不等
        - >, >=, <, <=: 数值比较
        - in, not_in: 列表包含
        - between: 区间（闭区间）
        - contains: 字符串包含
        - starts_with, ends_with: 字符串前缀/后缀
        - is_null: 空值判断
        - regex: 正则匹配
        """
        try:
            if op == "==":
                return actual == expected
            elif op == "!=":
                return actual != expected
            elif op == ">":
                return actual is not None and actual > expected
            elif op == ">=":
                return actual is not None and actual >= expected
            elif op == "<":
                return actual is not None and actual < expected
            elif op == "<=":
                return actual is not None and actual <= expected
            elif op == "in":
                return actual in expected if expected else False
            elif op == "not_in":
                return actual not in expected if expected else True
            elif op == "between":
                if actual is None or not isinstance(expected, (list, tuple)) or len(expected) != 2:
                    return False
                return expected[0] <= actual <= expected[1]
            elif op == "contains":
                return expected in str(actual) if actual is not None else False
            elif op == "starts_with":
                return str(actual).startswith(str(expected)) if actual is not None else False
            elif op == "ends_with":
                return str(actual).endswith(str(expected)) if actual is not None else False
            elif op == "is_null":
                return (actual is None) == expected
            elif op == "regex":
                import re
                return bool(re.match(expected, str(actual))) if actual is not None else False
            else:
                return False
        except (TypeError, ValueError):
            return False

    def resolve_approvers(
        self,
        node: ApprovalNodeDefinition,
        context: Dict[str, Any],
    ) -> List[int]:
        """
        解析审批人列表

        Args:
            node: 节点定义
            context: 上下文数据

        Returns:
            审批人ID列表
        """
        approver_type = node.approver_type
        config = node.approver_config or {}

        if approver_type == "FIXED_USER":
            # 指定用户
            return config.get("user_ids", [])

        elif approver_type == "ROLE":
            # 指定角色
            return self._resolve_role_approvers(config, context)

        elif approver_type == "DEPARTMENT_HEAD":
            # 部门主管
            return self._resolve_department_head(context)

        elif approver_type == "DIRECT_MANAGER":
            # 直属上级
            return self._resolve_direct_manager(context)

        elif approver_type == "FORM_FIELD":
            # 表单字段
            field_name = config.get("field_name")
            if field_name:
                form_data = context.get("form_data", {})
                user_id = form_data.get(field_name)
                if user_id:
                    return [user_id] if isinstance(user_id, int) else user_id
            return []

        elif approver_type == "MULTI_DEPT":
            # 多部门评估（ECN会签）
            return self._resolve_multi_dept_approvers(config, context)

        elif approver_type == "DYNAMIC":
            # 动态计算（通过适配器）
            adapter = context.get("adapter")
            if adapter and hasattr(adapter, "resolve_approvers"):
                return adapter.resolve_approvers(node, context)
            return []

        elif approver_type == "INITIATOR":
            # 发起人（用于退回到发起人）
            initiator = context.get("initiator")
            if initiator:
                return [initiator.get("id") or initiator.id]
            return []

        else:
            return []

    def _resolve_role_approvers(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[int]:
        """解析角色对应的用户"""
        from app.models.user import User, UserRole, Role

        role_codes = config.get("role_codes", [])
        if isinstance(role_codes, str):
            role_codes = [role_codes]

        if not role_codes:
            return []

        # 查询拥有指定角色的用户
        users = (
            self.db.query(User.id)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .filter(
                Role.code.in_(role_codes),
                User.is_active == True,
            )
            .all()
        )

        return [u.id for u in users]

    def _resolve_department_head(self, context: Dict[str, Any]) -> List[int]:
        """解析部门主管"""
        from app.models.organization import Department

        initiator = context.get("initiator", {})
        dept_id = initiator.get("dept_id") if isinstance(initiator, dict) else getattr(initiator, "dept_id", None)

        if not dept_id:
            return []

        dept = self.db.query(Department).filter(Department.id == dept_id).first()
        if dept and dept.manager_id:
            return [dept.manager_id]

        return []

    def _resolve_direct_manager(self, context: Dict[str, Any]) -> List[int]:
        """解析直属上级"""
        from app.models.user import User

        initiator = context.get("initiator", {})
        user_id = initiator.get("id") if isinstance(initiator, dict) else getattr(initiator, "id", None)

        if not user_id:
            return []

        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.manager_id:
            return [user.manager_id]

        return []

    def _resolve_multi_dept_approvers(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[int]:
        """解析多部门审批人（ECN评估场景）"""
        from app.models.organization import Department

        dept_names = config.get("departments", [])
        if not dept_names:
            return []

        # 查询指定部门的主管
        depts = (
            self.db.query(Department)
            .filter(
                Department.name.in_(dept_names),
                Department.is_active == True,
            )
            .all()
        )

        approvers = []
        for dept in depts:
            if dept.manager_id:
                approvers.append(dept.manager_id)

        return approvers

    def get_next_nodes(
        self,
        current_node: ApprovalNodeDefinition,
        context: Dict[str, Any],
    ) -> List[ApprovalNodeDefinition]:
        """
        获取下一个节点列表

        对于条件分支节点，根据条件表达式决定走哪个分支
        """
        flow_id = current_node.flow_id
        current_order = current_node.node_order

        # 获取所有后续节点
        next_nodes = (
            self.db.query(ApprovalNodeDefinition)
            .filter(
                ApprovalNodeDefinition.flow_id == flow_id,
                ApprovalNodeDefinition.node_order > current_order,
                ApprovalNodeDefinition.is_active == True,
            )
            .order_by(ApprovalNodeDefinition.node_order)
            .all()
        )

        if not next_nodes:
            return []

        # 如果下一个节点是条件分支节点，评估条件
        next_node = next_nodes[0]

        if next_node.node_type == "CONDITION":
            # 评估条件，找到匹配的分支
            return self._resolve_condition_branch(next_node, context)

        return [next_node]

    def _resolve_condition_branch(
        self,
        condition_node: ApprovalNodeDefinition,
        context: Dict[str, Any],
    ) -> List[ApprovalNodeDefinition]:
        """解析条件分支节点，返回匹配的分支节点"""
        branches = condition_node.approver_config or {}
        branches_config = branches.get("branches", [])

        for branch in branches_config:
            conditions = branch.get("conditions")
            target_node_id = branch.get("target_node_id")

            if conditions and self._evaluate_conditions(conditions, context):
                if target_node_id:
                    target = (
                        self.db.query(ApprovalNodeDefinition)
                        .filter(ApprovalNodeDefinition.id == target_node_id)
                        .first()
                    )
                    if target:
                        return [target]

        # 没有匹配的条件，走默认分支
        default_node_id = branches.get("default_node_id")
        if default_node_id:
            default_node = (
                self.db.query(ApprovalNodeDefinition)
                .filter(ApprovalNodeDefinition.id == default_node_id)
                .first()
            )
            if default_node:
                return [default_node]

        return []
