# -*- coding: utf-8 -*-
"""
Service层基类
业务逻辑层抽象
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.common.crud.repository import BaseRepository
from app.common.crud.exceptions import (
    raise_not_found,
    raise_already_exists,
)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseService(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]
):
    """Service基类"""

    def __init__(
        self, model: Type[ModelType], db: AsyncSession, resource_name: str = None
    ):
        """
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
            resource_name: 资源名称（用于错误消息）
        """
        self.model = model
        self.db = db
        self.resource_name = resource_name or model.__name__
        self.repository = BaseRepository(model, db, resource_name)

    async def get(
        self, id: int, *, load_relationships: Optional[List[str]] = None
    ) -> ResponseSchemaType:
        """
        获取单个对象

        Raises:
            HTTPException: 404 if not found
        """
        obj = await self.repository.get(id, load_relationships=load_relationships)
        if not obj:
            raise_not_found(self.resource_name, id)

        return self._to_response(obj)

    async def get_by_field(
        self,
        field_name: str,
        value: Any,
        *,
        load_relationships: Optional[List[str]] = None,
    ) -> Optional[ResponseSchemaType]:
        """
        根据字段值获取单个对象

        Returns:
            响应对象或None
        """
        obj = await self.repository.get_by_field(
            field_name, value, load_relationships=load_relationships
        )
        if not obj:
            return None

        return self._to_response(obj)

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        keyword: Optional[str] = None,
        keyword_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
        load_relationships: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        列表查询

        Returns:
            {
                "items": List[ResponseSchemaType],
                "total": int,
                "skip": int,
                "limit": int
            }
        """
        items, total = await self.repository.list(
            skip=skip,
            limit=limit,
            filters=filters,
            keyword=keyword,
            keyword_fields=keyword_fields,
            order_by=order_by,
            order_direction=order_direction,
            load_relationships=load_relationships,
        )

        return {
            "items": [self._to_response(item) for item in items],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def create(
        self, obj_in: CreateSchemaType, *, check_unique: Optional[Dict[str, Any]] = None
    ) -> ResponseSchemaType:
        """
        创建对象

        Args:
            obj_in: 创建数据
            check_unique: 唯一性检查字段，如 {"code": obj_in.code}

        Raises:
            HTTPException: 409 if already exists
        """
        # 唯一性检查
        if check_unique:
            for field, value in check_unique.items():
                exists = await self.repository.exists_by_field(field, value)
                if exists:
                    raise_already_exists(self.resource_name, field, str(value))

        # 创建前钩子（可扩展）
        obj_in = await self._before_create(obj_in)

        # 创建对象
        db_obj = await self.repository.create(obj_in)

        # 创建后钩子（可扩展）
        db_obj = await self._after_create(db_obj)

        # 记录审计日志
        await self._log_audit("CREATE", db_obj)

        return self._to_response(db_obj)

    async def update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
        *,
        check_unique: Optional[Dict[str, Any]] = None,
    ) -> ResponseSchemaType:
        """
        更新对象

        Args:
            id: 对象ID
            obj_in: 更新数据
            check_unique: 唯一性检查字段（排除当前对象）

        Raises:
            HTTPException: 404 if not found, 409 if conflict
        """
        # 检查存在性
        db_obj = await self.repository.get(id)
        if not db_obj:
            raise_not_found(self.resource_name, id)

        # 唯一性检查（排除当前对象）
        if check_unique:
            for field, value in check_unique.items():
                existing = await self.repository.get_by_field(field, value)
                if existing and existing.id != id:
                    raise_already_exists(self.resource_name, field, str(value))

        # 更新前钩子（可扩展）
        obj_in = await self._before_update(id, obj_in, db_obj)

        # 更新对象
        db_obj = await self.repository.update(id, obj_in)

        # 更新后钩子（可扩展）
        db_obj = await self._after_update(db_obj)

        # 记录审计日志
        await self._log_audit(
            "UPDATE", db_obj, changes=obj_in.model_dump(exclude_unset=True)
        )

        return self._to_response(db_obj)

    async def delete(self, id: int, *, soft_delete: bool = False) -> bool:
        """
        删除对象

        Args:
            id: 对象ID
            soft_delete: 是否软删除

        Raises:
            HTTPException: 404 if not found
        """
        # 检查存在性
        exists = await self.repository.exists(id)
        if not exists:
            raise_not_found(self.resource_name, id)

        # 删除前钩子（可扩展）
        await self._before_delete(id)

        # 删除对象
        success = await self.repository.delete(id, soft_delete=soft_delete)

        # 删除后钩子（可扩展）
        if success:
            # 记录审计日志
            await self._log_audit("DELETE", object_id=id)
            await self._after_delete(id)

        return success

    async def count(self, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计数量"""
        return await self.repository.count(filters=filters)

    # ========== 可扩展的钩子方法 ==========

    def _to_response(self, obj: ModelType) -> ResponseSchemaType:
        """
        将模型对象转换为响应对象

        子类可以重写此方法以实现自定义转换逻辑
        """
        # 注意：这是一个抽象方法，子类需要实现具体的转换逻辑
        # 因为ResponseSchemaType是TypeVar，不能直接实例化
        # 子类应该重写此方法，例如：
        # def _to_response(self, obj: Project) -> ProjectResponse:
        #     return ProjectResponse.model_validate(obj)
        raise NotImplementedError("子类必须实现_to_response方法")

    async def _before_create(self, obj_in: CreateSchemaType) -> CreateSchemaType:
        """创建前钩子（可扩展）"""
        return obj_in

    async def _after_create(self, db_obj: ModelType) -> ModelType:
        """创建后钩子（可扩展）"""
        return db_obj

    async def _before_update(
        self, id: int, obj_in: UpdateSchemaType, db_obj: ModelType
    ) -> UpdateSchemaType:
        """更新前钩子（可扩展）"""
        return obj_in

    async def _after_update(self, db_obj: ModelType) -> ModelType:
        """更新后钩子（可扩展）"""
        return db_obj

    async def _before_delete(self, id: int) -> None:
        """删除前钩子（可扩展）"""
        pass

    async def _after_delete(self, id: int) -> None:
        """删除后钩子（可扩展）"""
        pass

    async def _log_audit(
        self,
        action_type: str,
        db_obj: Optional[ModelType] = None,
        object_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        自动记录审计日志 (Async)
        """
        try:
            from app.common.context import get_audit_context
            from app.models.user import PermissionAudit
            import json

            ctx = get_audit_context()
            operator_id = ctx.get("operator_id")

            # 如果没有操作人ID，不记录
            if not operator_id:
                return

            target_id = object_id or getattr(db_obj, "id", None)
            if not target_id:
                return

            model_name = self.model.__name__
            action = f"{model_name.upper()}_{action_type}"

            # 构建详情
            detail = ctx.get("detail") or {}
            if changes:
                detail["changes"] = changes

            if not detail.get("description"):
                detail["description"] = (
                    f"{self.resource_name} {action_type.lower()}: {target_id}"
                )

            audit = PermissionAudit(
                operator_id=operator_id,
                action=action,
                target_type=model_name.lower(),
                target_id=target_id,
                detail=json.dumps(detail, ensure_ascii=False) if detail else None,
                ip_address=ctx.get("client_ip"),
                user_agent=ctx.get("user_agent"),
            )
            self.db.add(audit)
            # 因为这通常是在 create/update 之后，它们已经 commit 了，
            # 我们这里手动 commit 一下审计记录
            await self.db.commit()

        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to record async audit log: {e}"
            )
