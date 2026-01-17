# -*- coding: utf-8 -*-
"""
数据权限服务 v2 (Data Scope Service)

提供基于组织架构的数据权限过滤功能
"""

import logging
from typing import Any, List, Optional, Set, TypeVar

from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Query, Session

from app.models.organization_v2 import EmployeeOrgAssignment, OrganizationUnit
from app.models.permission_v2 import DataScopeRule, RoleDataScope, ScopeType
from app.models.user import User
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DataScopeServiceV2:
    """
    数据权限服务类 v2

    提供基于组织架构的数据权限过滤功能
    """

    @staticmethod
    def get_user_org_units(db: Session, user_id: int) -> List[int]:
        """
        获取用户所属的组织单元ID列表

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            组织单元ID列表
        """
        org_unit_ids: Set[int] = set()

        try:
            # 获取用户的组织分配
            assignments = db.query(EmployeeOrgAssignment).join(
                User, User.employee_id == EmployeeOrgAssignment.employee_id
            ).filter(
                User.id == user_id,
                EmployeeOrgAssignment.is_active == True
            ).all()

            for assignment in assignments:
                org_unit_ids.add(assignment.org_unit_id)

        except Exception as e:
            logger.warning(f"获取用户组织单元失败: {e}")

        return list(org_unit_ids)

    @staticmethod
    def get_accessible_org_units(
        db: Session,
        user_id: int,
        scope_type: str
    ) -> List[int]:
        """
        根据数据权限范围获取用户可访问的组织单元ID列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            scope_type: 权限范围类型

        Returns:
            可访问的组织单元ID列表
        """
        if scope_type == ScopeType.ALL.value:
            # 全部数据：返回所有组织单元
            units = db.query(OrganizationUnit.id).filter(
                OrganizationUnit.is_active == True
            ).all()
            return [u.id for u in units]

        # 获取用户所属的组织单元
        user_org_ids = DataScopeServiceV2.get_user_org_units(db, user_id)
        if not user_org_ids:
            return []

        accessible_ids: Set[int] = set()

        for org_id in user_org_ids:
            org_unit = db.query(OrganizationUnit).filter(
                OrganizationUnit.id == org_id
            ).first()

            if not org_unit:
                continue

            if scope_type == ScopeType.BUSINESS_UNIT.value:
                # 本事业部数据：向上找到事业部，然后获取所有下级
                bu = DataScopeServiceV2._find_ancestor_by_type(
                    db, org_unit, 'BUSINESS_UNIT'
                )
                if bu:
                    accessible_ids.update(
                        DataScopeServiceV2._get_subtree_ids(db, bu.id)
                    )
                else:
                    # 没有事业部，使用当前组织的子树
                    accessible_ids.update(
                        DataScopeServiceV2._get_subtree_ids(db, org_id)
                    )

            elif scope_type == ScopeType.DEPARTMENT.value:
                # 本部门数据：向上找到部门，然后获取所有下级
                dept = DataScopeServiceV2._find_ancestor_by_type(
                    db, org_unit, 'DEPARTMENT'
                )
                if dept:
                    accessible_ids.update(
                        DataScopeServiceV2._get_subtree_ids(db, dept.id)
                    )
                else:
                    accessible_ids.add(org_id)

            elif scope_type == ScopeType.TEAM.value:
                # 本团队数据：仅当前组织
                accessible_ids.add(org_id)

        return list(accessible_ids)

    @staticmethod
    def _find_ancestor_by_type(
        db: Session,
        org_unit: OrganizationUnit,
        unit_type: str
    ) -> Optional[OrganizationUnit]:
        """
        向上查找指定类型的祖先组织

        Args:
            db: 数据库会话
            org_unit: 当前组织单元
            unit_type: 目标类型

        Returns:
            祖先组织单元或 None
        """
        current = org_unit
        while current:
            if current.unit_type == unit_type:
                return current
            if current.parent_id:
                current = db.query(OrganizationUnit).filter(
                    OrganizationUnit.id == current.parent_id
                ).first()
            else:
                break
        return None

    @staticmethod
    def _get_subtree_ids(db: Session, org_unit_id: int) -> Set[int]:
        """
        获取组织单元的所有子节点ID（包括自己）

        Args:
            db: 数据库会话
            org_unit_id: 组织单元ID

        Returns:
            子节点ID集合
        """
        ids: Set[int] = {org_unit_id}

        # 使用路径前缀查询（如果有path字段）
        org_unit = db.query(OrganizationUnit).filter(
            OrganizationUnit.id == org_unit_id
        ).first()

        if org_unit and org_unit.path:
            # 使用路径前缀匹配
            children = db.query(OrganizationUnit.id).filter(
                OrganizationUnit.path.like(f"{org_unit.path}%"),
                OrganizationUnit.is_active == True
            ).all()
            ids.update([c.id for c in children])
        else:
            # 递归查询子节点
            children = db.query(OrganizationUnit).filter(
                OrganizationUnit.parent_id == org_unit_id,
                OrganizationUnit.is_active == True
            ).all()

            for child in children:
                ids.update(DataScopeServiceV2._get_subtree_ids(db, child.id))

        return ids

    @staticmethod
    def get_data_scope(
        db: Session,
        user_id: int,
        resource_type: str
    ) -> Optional[DataScopeRule]:
        """
        获取用户对指定资源的数据权限规则

        Args:
            db: 数据库会话
            user_id: 用户ID
            resource_type: 资源类型

        Returns:
            数据权限规则或 None
        """
        scopes = PermissionService.get_user_data_scopes(db, user_id)
        scope_type = scopes.get(resource_type)

        if not scope_type:
            return None

        return db.query(DataScopeRule).filter(
            DataScopeRule.scope_type == scope_type,
            DataScopeRule.is_active == True
        ).first()

    @staticmethod
    def apply_data_scope(
        query: Query,
        db: Session,
        user: User,
        resource_type: str,
        org_field: str = "org_unit_id",
        owner_field: str = "created_by",
        pm_field: Optional[str] = None
    ) -> Query:
        """
        应用数据权限过滤到查询

        Args:
            query: SQLAlchemy 查询对象
            db: 数据库会话
            user: 用户对象
            resource_type: 资源类型
            org_field: 组织字段名（默认 org_unit_id）
            owner_field: 所有者字段名（默认 created_by）
            pm_field: 项目经理字段名（可选）

        Returns:
            过滤后的查询对象
        """
        # 超级管理员不过滤
        if user.is_superuser:
            return query

        # 获取数据权限范围
        scopes = PermissionService.get_user_data_scopes(db, user.id)
        scope_type = scopes.get(resource_type, ScopeType.OWN.value)

        # 获取查询的模型类
        model_class = query.column_descriptions[0]['entity']

        if scope_type == ScopeType.ALL.value:
            # 全部数据，不过滤
            return query

        elif scope_type in [ScopeType.BUSINESS_UNIT.value, ScopeType.DEPARTMENT.value, ScopeType.TEAM.value]:
            # 基于组织的过滤
            accessible_org_ids = DataScopeServiceV2.get_accessible_org_units(
                db, user.id, scope_type
            )

            if not accessible_org_ids:
                # 没有可访问的组织，返回空查询
                return query.filter(False)

            # 检查模型是否有组织字段
            if hasattr(model_class, org_field):
                org_column = getattr(model_class, org_field)
                return query.filter(org_column.in_(accessible_org_ids))
            elif hasattr(model_class, 'department_id'):
                # 兼容旧的 department_id 字段
                return query.filter(model_class.department_id.in_(accessible_org_ids))
            else:
                # 没有组织字段，不过滤
                logger.warning(f"模型 {model_class.__name__} 没有组织字段，跳过数据权限过滤")
                return query

        elif scope_type == ScopeType.PROJECT.value:
            # 项目数据：检查用户是否是项目成员
            # 这需要关联项目成员表，暂时简化为检查 pm_id
            filters = []

            if hasattr(model_class, owner_field):
                filters.append(getattr(model_class, owner_field) == user.id)

            if pm_field and hasattr(model_class, pm_field):
                filters.append(getattr(model_class, pm_field) == user.id)

            if filters:
                return query.filter(or_(*filters))
            else:
                return query

        elif scope_type == ScopeType.OWN.value:
            # 仅个人数据
            filters = []

            if hasattr(model_class, owner_field):
                filters.append(getattr(model_class, owner_field) == user.id)

            if hasattr(model_class, 'owner_id'):
                filters.append(model_class.owner_id == user.id)

            if pm_field and hasattr(model_class, pm_field):
                filters.append(getattr(model_class, pm_field) == user.id)

            if filters:
                return query.filter(or_(*filters))
            else:
                # 没有所有者字段，返回空查询
                return query.filter(False)

        else:
            # 未知范围，默认返回个人数据
            if hasattr(model_class, owner_field):
                return query.filter(getattr(model_class, owner_field) == user.id)
            return query.filter(False)

    @staticmethod
    def can_access_data(
        db: Session,
        user: User,
        resource_type: str,
        data: Any,
        org_field: str = "org_unit_id",
        owner_field: str = "created_by"
    ) -> bool:
        """
        检查用户是否可以访问指定数据

        Args:
            db: 数据库会话
            user: 用户对象
            resource_type: 资源类型
            data: 数据对象
            org_field: 组织字段名
            owner_field: 所有者字段名

        Returns:
            是否可以访问
        """
        if user.is_superuser:
            return True

        # 获取数据权限范围
        scopes = PermissionService.get_user_data_scopes(db, user.id)
        scope_type = scopes.get(resource_type, ScopeType.OWN.value)

        if scope_type == ScopeType.ALL.value:
            return True

        elif scope_type in [ScopeType.BUSINESS_UNIT.value, ScopeType.DEPARTMENT.value, ScopeType.TEAM.value]:
            # 检查数据的组织是否在可访问范围内
            data_org_id = getattr(data, org_field, None) or getattr(data, 'department_id', None)
            if not data_org_id:
                return True  # 没有组织字段，默认允许

            accessible_org_ids = DataScopeServiceV2.get_accessible_org_units(
                db, user.id, scope_type
            )
            return data_org_id in accessible_org_ids

        elif scope_type == ScopeType.OWN.value:
            # 检查是否是所有者
            data_owner = getattr(data, owner_field, None)
            data_owner2 = getattr(data, 'owner_id', None)
            data_pm = getattr(data, 'pm_id', None)

            return user.id in [data_owner, data_owner2, data_pm]

        return False
