# -*- coding: utf-8 -*-
"""
数据权限服务 (Data Scope Service)

提供基于组织架构的数据权限过滤功能
"""

import logging
from typing import Any, List, Optional, Set, TypeVar

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.common.query_filters import apply_like_filter
from app.models.organization import EmployeeOrgAssignment, OrganizationUnit
from app.models.permission import ScopeType
from app.models.user import User
from app.services.permission_service import PermissionService
from app.services.data_scope.generic_filter import GenericFilterService

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DataScopeService:
    """
    数据权限服务类

    提供基于组织架构的数据权限过滤功能
    """

    @staticmethod
    def get_user_org_units(db: Session, user_id: int) -> List[int]:
        """
        获取用户所属的组织单元ID列表
        """
        org_unit_ids: Set[int] = set()

        try:
            assignments = (
                db.query(EmployeeOrgAssignment)
                .join(User, User.employee_id == EmployeeOrgAssignment.employee_id)
                .filter(User.id == user_id, EmployeeOrgAssignment.is_active)
                .all()
            )

            for assignment in assignments:
                org_unit_ids.add(assignment.org_unit_id)

        except Exception as e:
            logger.warning(f"获取用户组织单元失败: {e}")

        return list(org_unit_ids)

    @staticmethod
    def get_accessible_org_units(
        db: Session, user_id: int, scope_type: str
    ) -> List[int]:
        """
        根据数据权限范围获取用户可访问的组织单元ID列表
        """
        if scope_type == ScopeType.ALL.value:
            units = (
                db.query(OrganizationUnit.id).filter(OrganizationUnit.is_active).all()
            )
            return [u.id for u in units]

        user_org_ids = DataScopeService.get_user_org_units(db, user_id)
        if not user_org_ids:
            return []

        accessible_ids: Set[int] = set()

        for org_id in user_org_ids:
            org_unit = (
                db.query(OrganizationUnit).filter(OrganizationUnit.id == org_id).first()
            )

            if not org_unit:
                continue

            if scope_type == ScopeType.BUSINESS_UNIT.value:
                bu = DataScopeService._find_ancestor_by_type(
                    db, org_unit, "BUSINESS_UNIT"
                )
                if bu:
                    accessible_ids.update(DataScopeService._get_subtree_ids(db, bu.id))
                else:
                    accessible_ids.update(DataScopeService._get_subtree_ids(db, org_id))

            elif scope_type == ScopeType.DEPARTMENT.value:
                dept = DataScopeService._find_ancestor_by_type(
                    db, org_unit, "DEPARTMENT"
                )
                if dept:
                    accessible_ids.update(
                        DataScopeService._get_subtree_ids(db, dept.id)
                    )
                else:
                    accessible_ids.add(org_id)

            elif scope_type == ScopeType.TEAM.value:
                accessible_ids.add(org_id)

        return list(accessible_ids)

    @staticmethod
    def _find_ancestor_by_type(
        db: Session, org_unit: OrganizationUnit, unit_type: str
    ) -> Optional[OrganizationUnit]:
        """
        向上查找指定类型的祖先组织
        """
        current = org_unit
        while current:
            if current.unit_type == unit_type:
                return current
            if current.parent_id:
                current = (
                    db.query(OrganizationUnit)
                    .filter(OrganizationUnit.id == current.parent_id)
                    .first()
                )
            else:
                break
        return None

    @staticmethod
    def _get_subtree_ids(db: Session, org_unit_id: int) -> Set[int]:
        """
        获取组织单元的所有子节点ID（包括自己）
        """
        ids: Set[int] = {org_unit_id}

        org_unit = (
            db.query(OrganizationUnit)
            .filter(OrganizationUnit.id == org_unit_id)
            .first()
        )

        if org_unit and org_unit.path:
            children_query = db.query(OrganizationUnit.id).filter(OrganizationUnit.is_active)
            children_query = apply_like_filter(
                children_query,
                OrganizationUnit,
                f"{org_unit.path}%",
                "path",
                use_ilike=False,
            )
            children = children_query.all()
            ids.update([c.id for c in children])
        else:
            children = (
                db.query(OrganizationUnit)
                .filter(
                    OrganizationUnit.parent_id == org_unit_id,
                    OrganizationUnit.is_active,
                )
                .all()
            )

            for child in children:
                ids.update(DataScopeService._get_subtree_ids(db, child.id))

        return ids

    @staticmethod
    def apply_data_scope(
        query: Query,
        db: Session,
        user: User,
        resource_type: str,
        org_field: str = "org_unit_id",
        owner_field: str = "created_by",
        pm_field: Optional[str] = None,
    ) -> Query:
        """
        应用数据权限过滤到查询
        """
        if user.is_superuser:
            return query

        scopes = PermissionService.get_user_data_scopes(db, user.id)
        scope_type = scopes.get(resource_type, ScopeType.OWN.value)

        model_class = query.column_descriptions[0]["entity"]

        if scope_type == ScopeType.ALL.value:
            return query

        elif scope_type in [
            ScopeType.BUSINESS_UNIT.value,
            ScopeType.DEPARTMENT.value,
            ScopeType.TEAM.value,
        ]:
            accessible_org_ids = DataScopeService.get_accessible_org_units(
                db, user.id, scope_type
            )

            if not accessible_org_ids:
                return query.filter(False)

            if hasattr(model_class, org_field):
                org_column = getattr(model_class, org_field)
                return query.filter(org_column.in_(accessible_org_ids))
            elif hasattr(model_class, "department_id"):
                return query.filter(model_class.department_id.in_(accessible_org_ids))
            else:
                logger.warning(
                    f"模型 {model_class.__name__} 没有组织字段，跳过数据权限过滤"
                )
                return query

        elif scope_type == ScopeType.PROJECT.value:
            filters = []
            if hasattr(model_class, owner_field):
                filters.append(getattr(model_class, owner_field) == user.id)
            if pm_field and hasattr(model_class, pm_field):
                filters.append(getattr(model_class, pm_field) == user.id)

            return query.filter(or_(*filters)) if filters else query

        elif scope_type == ScopeType.OWN.value:
            filters = []
            if hasattr(model_class, owner_field):
                filters.append(getattr(model_class, owner_field) == user.id)
            if hasattr(model_class, "owner_id"):
                filters.append(model_class.owner_id == user.id)
            if pm_field and hasattr(model_class, pm_field):
                filters.append(getattr(model_class, pm_field) == user.id)

            return query.filter(or_(*filters)) if filters else query.filter(False)

        return query.filter(False)

    filter_by_scope = staticmethod(GenericFilterService.filter_by_scope)
    check_customer_access = staticmethod(GenericFilterService.check_customer_access)

    @staticmethod
    def can_access_data(
        db: Session,
        user: User,
        resource_type: str,
        data: Any,
        org_field: str = "org_unit_id",
        owner_field: str = "created_by",
    ) -> bool:
        """
        检查用户是否可以访问指定数据
        """
        if user.is_superuser:
            return True

        scopes = PermissionService.get_user_data_scopes(db, user.id)
        scope_type = scopes.get(resource_type, ScopeType.OWN.value)

        if scope_type == ScopeType.ALL.value:
            return True

        elif scope_type in [
            ScopeType.BUSINESS_UNIT.value,
            ScopeType.DEPARTMENT.value,
            ScopeType.TEAM.value,
        ]:
            data_org_id = getattr(data, org_field, None) or getattr(
                data, "department_id", None
            )
            if not data_org_id:
                return True

            accessible_org_ids = DataScopeService.get_accessible_org_units(
                db, user.id, scope_type
            )
            return data_org_id in accessible_org_ids

        elif scope_type == ScopeType.OWN.value:
            data_owner = getattr(data, owner_field, None)
            data_owner2 = getattr(data, "owner_id", None)
            data_pm = getattr(data, "pm_id", None)
            return user.id in [data_owner, data_owner2, data_pm]

        return False
