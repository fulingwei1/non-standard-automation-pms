# -*- coding: utf-8 -*-
"""
通用数据权限过滤方法
支持任意模型的数据权限过滤
"""

import logging
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScopeEnum
from app.models.project import Project
from app.models.user import User

from .config import DataScopeConfig
from .user_scope import UserScopeService

logger = logging.getLogger(__name__)


class GenericFilterService:
    """通用过滤服务"""

    @staticmethod
    def filter_by_scope(
        db: Session,
        query: Query,
        model: type,
        user: User,
        config: Optional[DataScopeConfig] = None
    ) -> Query:
        """
        通用数据权限过滤方法

        根据用户的数据权限范围和模型配置，自动过滤查询结果。

        Args:
            db: 数据库会话
            query: SQLAlchemy 查询对象
            model: 模型类（如 PurchaseOrder, AcceptanceOrder）
            user: 当前用户
            config: 数据权限配置，如果不提供则使用默认配置

        Returns:
            过滤后的查询对象

        使用示例:
            ```python
            # 基本用法
            query = GenericFilterService.filter_by_scope(db, query, PurchaseOrder, user)

            # 自定义配置
            config = DataScopeConfig(
                owner_field="requester_id",
                additional_owner_fields=["approver_id"],
                project_field="project_id"
            )
            query = GenericFilterService.filter_by_scope(db, query, PurchaseOrder, user, config)
            ```
        """
        if user.is_superuser:
            return query

        if config is None:
            config = DataScopeConfig()

        # 如果有自定义过滤函数，优先使用
        if config.custom_filter:
            data_scope = UserScopeService.get_user_data_scope(db, user)
            return config.custom_filter(query, user, data_scope, db)

        data_scope = UserScopeService.get_user_data_scope(db, user)

        if data_scope == DataScopeEnum.ALL.value:
            return query

        # 构建所有者字段列表
        owner_fields = []
        if config.owner_field and hasattr(model, config.owner_field):
            owner_fields.append(getattr(model, config.owner_field))
        if config.additional_owner_fields:
            for field_name in config.additional_owner_fields:
                if hasattr(model, field_name):
                    owner_fields.append(getattr(model, field_name))

        if data_scope == DataScopeEnum.OWN.value:
            # OWN：只看自己的数据
            if owner_fields:
                conditions = [field == user.id for field in owner_fields]
                return query.filter(or_(*conditions))
            # 如果没有所有者字段，返回空结果
            return query.filter(False)

        if data_scope == DataScopeEnum.SUBORDINATE.value:
            # SUBORDINATE：自己 + 直接下属的数据
            subordinate_ids = UserScopeService.get_subordinate_ids(db, user.id)
            allowed_user_ids = list(subordinate_ids | {user.id})
            if owner_fields:
                conditions = [field.in_(allowed_user_ids) for field in owner_fields]
                return query.filter(or_(*conditions))
            return query.filter(False)

        if data_scope == DataScopeEnum.PROJECT.value:
            # PROJECT：参与项目的数据
            user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
            conditions = []

            # 通过项目字段过滤
            if config.project_field and hasattr(model, config.project_field):
                project_col = getattr(model, config.project_field)
                if user_project_ids:
                    conditions.append(project_col.in_(list(user_project_ids)))

            # 加上自己创建的数据（兜底）
            if owner_fields:
                conditions.extend([field == user.id for field in owner_fields])

            if conditions:
                return query.filter(or_(*conditions))
            return query.filter(False)

        if data_scope == DataScopeEnum.DEPT.value:
            # DEPT：同部门的数据
            conditions = []

            # 方式1：直接通过 dept_field 过滤
            if config.dept_field and hasattr(model, config.dept_field):
                dept_col = getattr(model, config.dept_field)
                if user.department:
                    from app.models.organization import Department
                    dept = db.query(Department).filter(
                        Department.dept_name == user.department
                    ).first()
                    if dept:
                        conditions.append(dept_col == dept.id)

            # 方式2：通过项目间接获取部门
            elif config.dept_through_project and config.project_field and hasattr(model, config.project_field):
                project_col = getattr(model, config.project_field)
                if user.department:
                    from app.models.organization import Department
                    dept = db.query(Department).filter(
                        Department.dept_name == user.department
                    ).first()
                    if dept:
                        # 获取该部门的所有项目
                        dept_projects = db.query(Project.id).filter(
                            Project.dept_id == dept.id
                        ).all()
                        dept_project_ids = [p[0] for p in dept_projects]
                        if dept_project_ids:
                            conditions.append(project_col.in_(dept_project_ids))

            # 加上自己创建的数据（兜底）
            if owner_fields:
                conditions.extend([field == user.id for field in owner_fields])

            if conditions:
                return query.filter(or_(*conditions))
            # 没有条件时降级为 OWN
            if owner_fields:
                return query.filter(or_(*[field == user.id for field in owner_fields]))
            return query.filter(False)

        # CUSTOM：自定义规则
        if data_scope == "CUSTOM":
            try:
                from .custom_rule import CustomRuleService
                # 尝试获取自定义规则并应用
                custom_rule = CustomRuleService.get_custom_rule(
                    db, user.id, model.__tablename__
                )
                if custom_rule:
                    return CustomRuleService.apply_custom_filter(
                        query, db, user, custom_rule, model,
                        owner_field=config.owner_field or "created_by",
                        project_field=config.project_field or "project_id"
                    )
                else:
                    logger.warning(
                        f"用户 {user.id} 有 CUSTOM 权限但未找到规则，降级为 OWN"
                    )
            except Exception as e:
                logger.error(f"应用自定义规则失败: {e}")
            # 降级为 OWN
            if owner_fields:
                return query.filter(or_(*[field == user.id for field in owner_fields]))
            return query.filter(False)

        # 默认：OWN
        if owner_fields:
            conditions = [field == user.id for field in owner_fields]
            return query.filter(or_(*conditions))
        return query.filter(False)

    @staticmethod
    def check_customer_access(
        db: Session,
        user: User,
        customer_id: int
    ) -> bool:
        """
        检查用户是否有权限访问指定客户的数据

        Returns:
            True: 有权限
            False: 无权限
        """
        if user.is_superuser:
            return True

        data_scope = UserScopeService.get_user_data_scope(db, user)

        if data_scope == DataScopeEnum.ALL.value:
            return True
        elif data_scope == DataScopeEnum.CUSTOMER.value:
            # 客户门户：只能看自己客户的项目
            # 这里需要根据业务逻辑实现，暂时返回True
            return True
        else:
            # 其他范围：通过项目间接访问客户
            # 检查是否有该客户的项目且用户有权限
            user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
            if not user_project_ids:
                return False

            projects = (
                db.query(Project.customer_id)
                .filter(
                    Project.id.in_(user_project_ids),
                    Project.customer_id == customer_id
                )
                .first()
            )
            return projects is not None
