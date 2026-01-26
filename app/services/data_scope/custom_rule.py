# -*- coding: utf-8 -*-
"""
自定义数据权限规则处理

支持 CUSTOM 类型的数据权限规则，基于 scope_config JSON 配置进行过滤

scope_config 结构示例:
{
    "filter_type": "user_list" | "org_unit_list" | "project_list" | "sql_expression",
    "conditions": [
        {"type": "user_ids", "values": [1, 2, 3]},
        {"type": "org_unit_ids", "values": [10, 20]},
        {"type": "project_ids", "values": [100, 200]},
        {"type": "created_by_field", "field": "created_by"},  # 使用配置的字段
    ],
    "combine_logic": "OR" | "AND",  # 默认 OR
    "include_owner": true  # 是否包含自己创建的数据
}
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Query, Session

from app.models.permission import DataScopeRule, RoleDataScope
from app.models.user import User

logger = logging.getLogger(__name__)


class CustomRuleService:
    """自定义规则服务"""

    @staticmethod
    def get_custom_rule(
        db: Session,
        user_id: int,
        resource_type: str
    ) -> Optional[DataScopeRule]:
        """
        获取用户对指定资源的自定义规则

        Args:
            db: 数据库会话
            user_id: 用户ID
            resource_type: 资源类型

        Returns:
            DataScopeRule 或 None
        """
        try:
            from app.services.permission_service import PermissionService

            # 获取用户的有效角色
            roles = PermissionService.get_user_effective_roles(db, user_id)
            role_ids = [r.id for r in roles]

            if not role_ids:
                return None

            # 查找资源级的数据权限配置
            role_data_scope = db.query(RoleDataScope).filter(
                RoleDataScope.role_id.in_(role_ids),
                RoleDataScope.resource_type == resource_type,
                RoleDataScope.is_active == True
            ).first()

            if not role_data_scope:
                return None

            # 获取关联的规则
            rule = db.query(DataScopeRule).filter(
                DataScopeRule.id == role_data_scope.scope_rule_id,
                DataScopeRule.scope_type == "CUSTOM",
                DataScopeRule.is_active == True
            ).first()

            return rule

        except Exception as e:
            logger.error(f"获取自定义规则失败: {e}")
            return None

    @staticmethod
    def apply_custom_filter(
        query: Query,
        db: Session,
        user: User,
        rule: DataScopeRule,
        model: type,
        owner_field: str = "created_by",
        org_field: str = "org_unit_id",
        project_field: str = "project_id"
    ) -> Query:
        """
        应用自定义规则过滤

        Args:
            query: SQLAlchemy 查询对象
            db: 数据库会话
            user: 当前用户
            rule: 数据权限规则
            model: 模型类
            owner_field: 所有者字段名
            org_field: 组织单元字段名
            project_field: 项目字段名

        Returns:
            过滤后的查询对象
        """
        config = rule.get_scope_config_dict()
        if not config:
            logger.warning(f"自定义规则 {rule.rule_code} 没有配置 scope_config")
            # 降级为仅个人数据
            if hasattr(model, owner_field):
                return query.filter(getattr(model, owner_field) == user.id)
            return query.filter(False)

        conditions = config.get("conditions", [])
        combine_logic = config.get("combine_logic", "OR")
        include_owner = config.get("include_owner", True)

        filter_conditions = []

        for condition in conditions:
            cond_type = condition.get("type")
            values = condition.get("values", [])

            if cond_type == "user_ids" and values:
                # 按用户ID列表过滤
                if hasattr(model, owner_field):
                    filter_conditions.append(
                        getattr(model, owner_field).in_(values)
                    )

            elif cond_type == "org_unit_ids" and values:
                # 按组织单元ID列表过滤
                if hasattr(model, org_field):
                    filter_conditions.append(
                        getattr(model, org_field).in_(values)
                    )
                elif hasattr(model, "department_id"):
                    filter_conditions.append(model.department_id.in_(values))

            elif cond_type == "project_ids" and values:
                # 按项目ID列表过滤
                if hasattr(model, project_field):
                    filter_conditions.append(
                        getattr(model, project_field).in_(values)
                    )

            elif cond_type == "created_by_field":
                # 使用指定字段作为创建者字段
                field_name = condition.get("field", owner_field)
                if hasattr(model, field_name):
                    filter_conditions.append(
                        getattr(model, field_name) == user.id
                    )

            elif cond_type == "sql_expression":
                # 原始SQL表达式（谨慎使用）
                expr = condition.get("expression")
                if expr:
                    # 替换占位符
                    expr = expr.replace("{{user_id}}", str(user.id))
                    filter_conditions.append(text(expr))

        # 包含创建者自己的数据
        if include_owner and hasattr(model, owner_field):
            filter_conditions.append(
                getattr(model, owner_field) == user.id
            )

        if not filter_conditions:
            # 没有有效条件，返回空结果
            return query.filter(False)

        # 组合条件
        if combine_logic == "AND":
            return query.filter(and_(*filter_conditions))
        else:
            return query.filter(or_(*filter_conditions))

    @staticmethod
    def validate_scope_config(config: Dict[str, Any]) -> List[str]:
        """
        验证 scope_config 配置的有效性

        Args:
            config: scope_config 配置

        Returns:
            错误信息列表，空列表表示有效
        """
        errors = []

        if not isinstance(config, dict):
            errors.append("scope_config 必须是字典类型")
            return errors

        conditions = config.get("conditions", [])
        if not isinstance(conditions, list):
            errors.append("conditions 必须是数组类型")
            return errors

        valid_types = {
            "user_ids", "org_unit_ids", "project_ids",
            "created_by_field", "sql_expression"
        }

        for i, cond in enumerate(conditions):
            if not isinstance(cond, dict):
                errors.append(f"conditions[{i}] 必须是字典类型")
                continue

            cond_type = cond.get("type")
            if not cond_type:
                errors.append(f"conditions[{i}] 缺少 type 字段")
            elif cond_type not in valid_types:
                errors.append(
                    f"conditions[{i}].type '{cond_type}' 无效，"
                    f"有效值: {valid_types}"
                )

            if cond_type in {"user_ids", "org_unit_ids", "project_ids"}:
                values = cond.get("values", [])
                if not isinstance(values, list):
                    errors.append(f"conditions[{i}].values 必须是数组类型")
                elif not values:
                    errors.append(f"conditions[{i}].values 不能为空")

        combine_logic = config.get("combine_logic", "OR")
        if combine_logic not in {"OR", "AND"}:
            errors.append("combine_logic 无效，有效值: OR, AND")

        return errors


__all__ = ["CustomRuleService"]
