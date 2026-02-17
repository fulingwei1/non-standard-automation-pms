# -*- coding: utf-8 -*-
"""
租户业务逻辑服务 (Tenant Service)

提供租户的创建、初始化、管理等功能。
"""

import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core.security import get_password_hash
from app.models.tenant import Tenant, TenantStatus, TenantPlan
from app.models.user import Role, RoleTemplate, User, UserRole
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantInitRequest,
)
from app.utils.db_helpers import save_obj

logger = logging.getLogger(__name__)


class TenantService:
    """租户服务类"""

    def __init__(self, db: Session):
        self.db = db

    def generate_tenant_code(self) -> str:
        """生成唯一的租户编码"""
        while True:
            code = f"T{uuid.uuid4().hex[:8].upper()}"
            existing = self.db.query(Tenant).filter(Tenant.tenant_code == code).first()
            if not existing:
                return code

    def create_tenant(self, tenant_in: TenantCreate) -> Tenant:
        """创建租户"""
        # 生成租户编码
        tenant_code = tenant_in.tenant_code or self.generate_tenant_code()

        # 检查编码是否已存在
        existing = self.db.query(Tenant).filter(Tenant.tenant_code == tenant_code).first()
        if existing:
            raise ValueError(f"租户编码 {tenant_code} 已存在")

        # 获取套餐限制
        plan_limits = {
            TenantPlan.FREE.value: {"users": 5, "roles": 5, "storage_gb": 1},
            TenantPlan.STANDARD.value: {"users": 50, "roles": 20, "storage_gb": 10},
            TenantPlan.ENTERPRISE.value: {"users": -1, "roles": -1, "storage_gb": 100},
        }
        limits = plan_limits.get(tenant_in.plan_type, plan_limits[TenantPlan.FREE.value])

        tenant = Tenant(
            tenant_code=tenant_code,
            tenant_name=tenant_in.tenant_name,
            plan_type=tenant_in.plan_type,
            max_users=tenant_in.max_users or limits["users"],
            max_roles=tenant_in.max_roles or limits["roles"],
            max_storage_gb=limits["storage_gb"],
            contact_name=tenant_in.contact_name,
            contact_email=tenant_in.contact_email,
            contact_phone=tenant_in.contact_phone,
            settings=tenant_in.settings,
            expired_at=tenant_in.expired_at,
        )

        save_obj(self.db, tenant)

        logger.info(f"创建租户成功: {tenant.tenant_code} - {tenant.tenant_name}")
        return tenant

    def get_tenant(self, tenant_id: int) -> Optional[Tenant]:
        """获取租户"""
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def get_tenant_by_code(self, tenant_code: str) -> Optional[Tenant]:
        """根据编码获取租户"""
        return self.db.query(Tenant).filter(Tenant.tenant_code == tenant_code).first()

    def list_tenants(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取租户列表"""
        query = self.db.query(Tenant)

        if status:
            query = query.filter(Tenant.status == status)

        query = apply_keyword_filter(query, Tenant, keyword, ["tenant_code", "tenant_name"])

        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = query.order_by(Tenant.created_at.desc())
        query = apply_pagination(query, pagination.offset, pagination.limit)
        items = query.all()

        return {
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pagination.pages_for_total(total),
        }

    def update_tenant(self, tenant_id: int, tenant_in: TenantUpdate) -> Optional[Tenant]:
        """更新租户"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        update_data = tenant_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        self.db.commit()
        self.db.refresh(tenant)

        logger.info(f"更新租户成功: {tenant.tenant_code}")
        return tenant

    def delete_tenant(self, tenant_id: int) -> bool:
        """删除租户（软删除）"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.DELETED.value
        self.db.commit()

        logger.info(f"删除租户成功: {tenant.tenant_code}")
        return True

    def init_tenant(self, tenant_id: int, init_data: TenantInitRequest) -> Dict[str, Any]:
        """初始化租户数据"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError("租户不存在")

        result = {
            "tenant_id": tenant_id,
            "roles_created": 0,
            "admin_created": False,
        }

        # 1. 复制角色模板
        if init_data.copy_role_templates:
            templates = self.db.query(RoleTemplate).filter(RoleTemplate.is_active).all()
            for template in templates:
                # 检查角色是否已存在
                existing_role = self.db.query(Role).filter(
                    Role.tenant_id == tenant_id,
                    Role.role_code == template.role_code
                ).first()

                if not existing_role:
                    role = Role(
                        tenant_id=tenant_id,
                        source_template_id=template.id,
                        role_code=template.role_code,
                        role_name=template.role_name,
                        description=template.description,
                        data_scope=template.data_scope,
                        nav_groups=template.nav_groups,
                        ui_config=template.ui_config,
                        sort_order=template.sort_order,
                        is_active=True,
                    )
                    self.db.add(role)
                    result["roles_created"] += 1

            self.db.flush()

        # 2. 创建租户管理员
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(User.username == init_data.admin_username).first()
        if existing_user:
            raise ValueError(f"用户名 {init_data.admin_username} 已存在")

        # 创建员工记录（简化处理）
        from app.models.organization import Employee
        employee = Employee(
            name=init_data.admin_real_name or init_data.admin_username,
            email=init_data.admin_email,
            status="ACTIVE",
        )
        self.db.add(employee)
        self.db.flush()

        # 创建用户
        admin_user = User(
            tenant_id=tenant_id,
            employee_id=employee.id,
            username=init_data.admin_username,
            password_hash=get_password_hash(init_data.admin_password),
            email=init_data.admin_email,
            real_name=init_data.admin_real_name or init_data.admin_username,
            is_active=True,
            is_tenant_admin=True,
        )
        self.db.add(admin_user)
        self.db.flush()

        # 分配 TENANT_ADMIN 角色
        tenant_admin_role = self.db.query(Role).filter(
            Role.tenant_id == tenant_id,
            Role.role_code == "TENANT_ADMIN"
        ).first()

        if tenant_admin_role:
            user_role = UserRole(user_id=admin_user.id, role_id=tenant_admin_role.id)
            self.db.add(user_role)

        result["admin_created"] = True
        result["admin_user_id"] = admin_user.id

        self.db.commit()

        logger.info(f"初始化租户成功: {tenant.tenant_code}, 创建角色: {result['roles_created']}")
        return result

    def get_tenant_stats(self, tenant_id: int) -> Optional[Dict[str, Any]]:
        """获取租户统计信��"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        user_count = self.db.query(func.count(User.id)).filter(User.tenant_id == tenant_id).scalar()
        role_count = self.db.query(func.count(Role.id)).filter(Role.tenant_id == tenant_id).scalar()

        # 项目数量
        # 注意：当前 Project 模型未实现 tenant_id 字段
        # 暂时统计与该租户用户创建的项目（通过 created_by 关联）
        project_count = 0
        try:
            from app.models.project import Project
            # 获取该租户的所有用户ID
            tenant_user_ids = self.db.query(User.id).filter(User.tenant_id == tenant_id).subquery()
            project_count = self.db.query(func.count(Project.id)).filter(
                Project.created_by.in_(tenant_user_ids)
            ).scalar() or 0
        except Exception:
            pass

        # 存储使用统计（基于附件表统计）
        storage_used_mb = 0
        try:
            from app.models.document import Attachment
            # 统计该租户用户上传的附件大小
            tenant_user_ids = self.db.query(User.id).filter(User.tenant_id == tenant_id).subquery()
            total_bytes = self.db.query(func.sum(Attachment.file_size)).filter(
                Attachment.uploaded_by.in_(tenant_user_ids)
            ).scalar() or 0
            storage_used_mb = round(total_bytes / (1024 * 1024), 2)
        except Exception:
            # 如果 Attachment 模型不存在或查询失败，返回0
            pass

        return {
            "tenant_id": tenant_id,
            "tenant_code": tenant.tenant_code,
            "user_count": user_count or 0,
            "role_count": role_count or 0,
            "project_count": project_count,
            "storage_used_mb": storage_used_mb,
            "plan_limits": tenant.get_plan_limits(),
        }
