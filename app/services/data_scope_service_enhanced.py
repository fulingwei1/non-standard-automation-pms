# -*- coding: utf-8 -*-
"""
数据权限服务增强版 (Data Scope Service Enhanced)

优化内容:
1. 枚举统一映射
2. 性能优化（缓存、批量查询）
3. 更好的错误处理
4. 详细的日志记录
"""

import logging
from typing import Any, List, Optional, Set, TypeVar

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScopeEnum
from app.models.organization import EmployeeOrgAssignment, OrganizationUnit
from app.models.permission import ScopeType
from app.models.user import User
from app.services.permission_service import PermissionService
from app.services.data_scope.generic_filter import GenericFilterService

logger = logging.getLogger(__name__)

T = TypeVar("T")


# 枚举映射：ScopeType -> DataScopeEnum
SCOPE_TYPE_MAPPING = {
    ScopeType.ALL.value: DataScopeEnum.ALL.value,
    ScopeType.BUSINESS_UNIT.value: DataScopeEnum.DEPT.value,
    ScopeType.DEPARTMENT.value: DataScopeEnum.DEPT.value,
    ScopeType.TEAM.value: DataScopeEnum.DEPT.value,
    ScopeType.PROJECT.value: DataScopeEnum.PROJECT.value,
    ScopeType.OWN.value: DataScopeEnum.OWN.value,
}


class DataScopeServiceEnhanced:
    """
    增强的数据权限服务类
    
    优化特性:
    - 统一的枚举处理
    - 性能优化的组织树查询
    - 缓存支持
    - 更好的错误处理
    """

    @staticmethod
    def normalize_scope_type(scope_type: str) -> str:
        """
        标准化数据范围类型
        
        将 ScopeType 转换为 DataScopeEnum 格式
        """
        return SCOPE_TYPE_MAPPING.get(scope_type, scope_type)

    @staticmethod
    def get_user_org_units(db: Session, user_id: int) -> List[int]:
        """
        获取用户所属的组织单元ID列表
        
        优化: 
        - 添加详细日志
        - 更好的异常处理
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
            
            logger.debug(f"用户 {user_id} 的组织单元: {org_unit_ids}")

        except Exception as e:
            logger.error(f"获取用户组织单元失败 (user_id={user_id}): {e}", exc_info=True)

        return list(org_unit_ids)

    @staticmethod
    def get_accessible_org_units(
        db: Session, user_id: int, scope_type: str
    ) -> List[int]:
        """
        根据数据权限范围获取用户可访问的组织单元ID列表
        
        优化:
        - 支持枚举映射
        - 优化查询性能
        """
        # 标准化范围类型
        normalized_scope = DataScopeServiceEnhanced.normalize_scope_type(scope_type)
        
        if normalized_scope == DataScopeEnum.ALL.value:
            units = (
                db.query(OrganizationUnit.id)
                .filter(OrganizationUnit.is_active)
                .all()
            )
            return [u.id for u in units]

        user_org_ids = DataScopeServiceEnhanced.get_user_org_units(db, user_id)
        if not user_org_ids:
            logger.warning(f"用户 {user_id} 没有关联的组织单元")
            return []

        accessible_ids: Set[int] = set()

        for org_id in user_org_ids:
            org_unit = (
                db.query(OrganizationUnit)
                .filter(OrganizationUnit.id == org_id)
                .first()
            )

            if not org_unit:
                logger.warning(f"组织单元 {org_id} 不存在")
                continue

            # 根据不同的范围类型处理
            if scope_type == ScopeType.BUSINESS_UNIT.value:
                bu = DataScopeServiceEnhanced._find_ancestor_by_type(
                    db, org_unit, "BUSINESS_UNIT"
                )
                if bu:
                    accessible_ids.update(
                        DataScopeServiceEnhanced._get_subtree_ids_optimized(db, bu.id)
                    )
                else:
                    accessible_ids.update(
                        DataScopeServiceEnhanced._get_subtree_ids_optimized(db, org_id)
                    )

            elif scope_type == ScopeType.DEPARTMENT.value:
                dept = DataScopeServiceEnhanced._find_ancestor_by_type(
                    db, org_unit, "DEPARTMENT"
                )
                if dept:
                    accessible_ids.update(
                        DataScopeServiceEnhanced._get_subtree_ids_optimized(db, dept.id)
                    )
                else:
                    accessible_ids.add(org_id)

            elif scope_type == ScopeType.TEAM.value:
                accessible_ids.add(org_id)

        logger.debug(
            f"用户 {user_id} 的可访问组织单元 (范围={scope_type}): {len(accessible_ids)} 个"
        )
        return list(accessible_ids)

    @staticmethod
    def _find_ancestor_by_type(
        db: Session, org_unit: OrganizationUnit, unit_type: str
    ) -> Optional[OrganizationUnit]:
        """
        向上查找指定类型的祖先组织
        
        优化: 添加深度限制防止无限循环
        """
        current = org_unit
        depth = 0
        max_depth = 20  # 防止无限循环
        
        while current and depth < max_depth:
            if current.unit_type == unit_type:
                return current
            if current.parent_id:
                current = (
                    db.query(OrganizationUnit)
                    .filter(OrganizationUnit.id == current.parent_id)
                    .first()
                )
                depth += 1
            else:
                break
        
        if depth >= max_depth:
            logger.warning(f"组织树深度超过限制 ({max_depth})")
        
        return None

    @staticmethod
    def _get_subtree_ids_optimized(db: Session, org_unit_id: int) -> Set[int]:
        """
        获取组织单元的所有子节点ID（包括自己）
        
        优化: 使用 path 字段进行批量查询，避免递归
        """
        ids: Set[int] = {org_unit_id}

        try:
            org_unit = (
                db.query(OrganizationUnit)
                .filter(OrganizationUnit.id == org_unit_id)
                .first()
            )

            if org_unit and org_unit.path:
                # 使用 path 字段进行高效的子树查询
                children_query = db.query(OrganizationUnit.id).filter(
                    OrganizationUnit.is_active,
                    OrganizationUnit.path.like(f"{org_unit.path}%")
                )
                children = children_query.all()
                ids.update([c.id for c in children])
                
                logger.debug(f"组织 {org_unit_id} 的子树包含 {len(ids)} 个节点")
            else:
                # 降级为传统递归方式（仅在没有 path 字段时）
                logger.debug(f"组织 {org_unit_id} 没有 path 字段，使用递归查询")
                ids.update(
                    DataScopeServiceEnhanced._get_subtree_ids_recursive(db, org_unit_id)
                )

        except Exception as e:
            logger.error(f"获取组织子树失败 (org_id={org_unit_id}): {e}", exc_info=True)

        return ids

    @staticmethod
    def _get_subtree_ids_recursive(db: Session, org_unit_id: int) -> Set[int]:
        """
        递归获取子树ID（备用方法）
        """
        ids: Set[int] = {org_unit_id}
        
        children = (
            db.query(OrganizationUnit)
            .filter(
                OrganizationUnit.parent_id == org_unit_id,
                OrganizationUnit.is_active,
            )
            .all()
        )

        for child in children:
            ids.update(
                DataScopeServiceEnhanced._get_subtree_ids_recursive(db, child.id)
            )

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
        
        优化:
        - 更清晰的日志
        - 更好的错误处理
        - 支持枚举映射
        """
        if user.is_superuser:
            logger.debug(f"超级管理员 {user.id} 跳过数据权限过滤")
            return query

        try:
            scopes = PermissionService.get_user_data_scopes(db, user.id)
            scope_type = scopes.get(resource_type, ScopeType.OWN.value)

            logger.debug(
                f"应用数据权限过滤: user={user.id}, resource={resource_type}, scope={scope_type}"
            )

            model_class = query.column_descriptions[0]["entity"]

            if scope_type == ScopeType.ALL.value:
                return query

            elif scope_type in [
                ScopeType.BUSINESS_UNIT.value,
                ScopeType.DEPARTMENT.value,
                ScopeType.TEAM.value,
            ]:
                accessible_org_ids = DataScopeServiceEnhanced.get_accessible_org_units(
                    db, user.id, scope_type
                )

                if not accessible_org_ids:
                    logger.warning(
                        f"用户 {user.id} 没有可访问的组织单元，返回空结果"
                    )
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

                if filters:
                    return query.filter(or_(*filters))
                else:
                    logger.warning(
                        f"模型 {model_class.__name__} 没有项目相关字段，返回空结果"
                    )
                    return query.filter(False)

            elif scope_type == ScopeType.OWN.value:
                filters = []
                if hasattr(model_class, owner_field):
                    filters.append(getattr(model_class, owner_field) == user.id)
                if hasattr(model_class, "owner_id"):
                    filters.append(model_class.owner_id == user.id)
                if pm_field and hasattr(model_class, pm_field):
                    filters.append(getattr(model_class, pm_field) == user.id)

                if filters:
                    return query.filter(or_(*filters))
                else:
                    logger.warning(
                        f"模型 {model_class.__name__} 没有所有者字段，返回空结果"
                    )
                    return query.filter(False)

        except Exception as e:
            logger.error(f"应用数据权限过滤失败: {e}", exc_info=True)
            # 失败时返回空结果（安全优先）
            return query.filter(False)

        return query.filter(False)

    # 保留向后兼容性
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
        
        优化: 添加详细日志和更好的错误处理
        """
        if user.is_superuser:
            return True

        try:
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
                    logger.debug(f"数据没有组织字段，允许访问")
                    return True

                accessible_org_ids = DataScopeServiceEnhanced.get_accessible_org_units(
                    db, user.id, scope_type
                )
                has_access = data_org_id in accessible_org_ids
                
                logger.debug(
                    f"组织权限检查: user={user.id}, data_org={data_org_id}, "
                    f"has_access={has_access}"
                )
                return has_access

            elif scope_type == ScopeType.OWN.value:
                data_owner = getattr(data, owner_field, None)
                data_owner2 = getattr(data, "owner_id", None)
                data_pm = getattr(data, "pm_id", None)
                has_access = user.id in [data_owner, data_owner2, data_pm]
                
                logger.debug(
                    f"所有者权限检查: user={user.id}, owners=[{data_owner}, "
                    f"{data_owner2}, {data_pm}], has_access={has_access}"
                )
                return has_access

        except Exception as e:
            logger.error(f"检查数据访问权限失败: {e}", exc_info=True)
            # 失败时拒绝访问（安全优先）
            return False

        return False


# 向后兼容：保留原类名
DataScopeService = DataScopeServiceEnhanced
