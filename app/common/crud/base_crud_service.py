# -*- coding: utf-8 -*-
"""
Synchronous Base CRUD service with integrated query handling.

This class builds on the repository/query builder primitives so that each
business module can inherit and immediately get pagination, filtering,
sorting, soft delete helpers, and lifecycle hooks.
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.crud.exceptions import raise_already_exists, raise_not_found
from app.common.crud.sync_repository import SyncBaseRepository
from app.common.crud.types import PaginatedResult, QueryParams, SortOrder

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)

UniqueCheckType = Optional[Union[Dict[str, Any], Sequence[str], str]]


class BaseCRUDService(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]
):
    """
    Sync CRUD service with unified pagination/query semantics.

    Subclasses usually only need to pass model + schemas and optionally tweak
    `search_fields` / `default_sort_field`.
    """

    #: Default search fields when QueryParams.search_fields is not supplied.
    search_fields: Sequence[str] = ()
    #: Restrict the filterable columns. Empty/None means allow any declared column.
    allowed_filter_fields: Optional[Sequence[str]] = None
    #: Restrict sortable columns. Empty/None means allow any declared column.
    allowed_sort_fields: Optional[Sequence[str]] = None
    #: Default column for ORDER BY when caller does not specify one.
    default_sort_field: Optional[str] = "created_at"
    #: Default sort order for ORDER BY.
    default_sort_order: SortOrder = SortOrder.DESC
    #: Column used for soft delete filtering (None disables automatic handling).
    soft_delete_field: Optional[str] = "deleted_at"
    #: Field names that must remain unique by default (Single-column constraints).
    unique_fields: Sequence[str] = ()

    def __init__(
        self,
        *,
        model: Type[ModelType],
        db: Session,
        response_schema: Type[ResponseSchemaType],
        resource_name: Optional[str] = None,
        default_filters: Optional[Dict[str, Any]] = None,
    ):
        self.model = model
        self.db = db
        self.resource_name = resource_name or model.__name__
        self.response_schema = response_schema
        self.repository = SyncBaseRepository(model, db, self.resource_name)
        self._default_filters = default_filters.copy() if default_filters else {}

    # --------------------------------------------------------------------- #
    # Read operations
    # --------------------------------------------------------------------- #
    def get(
        self,
        object_id: int,
        *,
        load_relationships: Optional[Sequence[str]] = None,
    ) -> ResponseSchemaType:
        relationships = list(load_relationships) if load_relationships else None
        obj = self.repository.get(object_id, load_relationships=relationships)
        if not obj:
            raise_not_found(self.resource_name, object_id)
        return self._to_response(obj)

    def list(
        self,
        params: Optional[QueryParams] = None,
        *,
        extra_filters: Optional[Dict[str, Any]] = None,
    ) -> PaginatedResult[ResponseSchemaType]:
        params = params or QueryParams()
        params = self._before_list(params)

        filters = self._merge_filters(params, extra_filters)
        if params.include_deleted and filters:
            filters.pop(self.soft_delete_field, None)

        search_fields = params.search_fields or self.search_fields
        order_by, order_direction = self._resolve_sorting(params)

        items, total = self.repository.list(
            skip=params.skip,
            limit=params.limit,
            filters=filters or None,
            keyword=params.search,
            keyword_fields=list(search_fields) if search_fields else None,
            order_by=order_by,
            order_direction=order_direction,
            load_relationships=params.load_relationships,
        )

        response_items = [self._to_response(item) for item in items]
        result = PaginatedResult(
            items=response_items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
        return self._after_list(result, params)

    def count(self, *, filters: Optional[Dict[str, Any]] = None) -> int:
        query_filters = self._merge_filters(QueryParams(), filters)
        return self.repository.count(filters=query_filters or None)

    # --------------------------------------------------------------------- #
    # Write operations
    # --------------------------------------------------------------------- #
    def create(
        self,
        obj_in: CreateSchemaType,
        *,
        check_unique: UniqueCheckType = None,
    ) -> ResponseSchemaType:
        processed_in = self._before_create(obj_in)
        self._ensure_unique(self.unique_fields, data=processed_in)
        self._ensure_unique(check_unique, data=processed_in)
        db_obj = self.repository.create(processed_in)

        # Detect initial status
        initial_status = getattr(db_obj, "status", None)
        if initial_status:
            self._on_status_change(db_obj, None, str(initial_status))

        db_obj = self._after_create(db_obj)

        # 记录审计日志
        self._log_audit("CREATE", db_obj)

        return self._to_response(db_obj)

    def bulk_create(
        self,
        objs_in: Sequence[CreateSchemaType],
    ) -> List[ResponseSchemaType]:
        processed = [self._before_create(obj) for obj in objs_in]
        db_objs = self.repository.create_many(processed)
        responses: List[ResponseSchemaType] = []
        for db_obj in db_objs:
            processed_obj = self._after_create(db_obj)
            responses.append(self._to_response(processed_obj))
        return responses

    def update(
        self,
        object_id: int,
        obj_in: UpdateSchemaType,
        *,
        check_unique: UniqueCheckType = None,
    ) -> ResponseSchemaType:
        db_obj = self.repository.get(object_id)
        if not db_obj:
            raise_not_found(self.resource_name, object_id)

        processed_in = self._before_update(object_id, obj_in, db_obj)
        # Capture old status
        old_status = getattr(db_obj, "status", None)

        self._ensure_unique(self.unique_fields, data=processed_in, current_id=object_id)
        self._ensure_unique(check_unique, data=processed_in, current_id=object_id)
        db_obj = self.repository.update(object_id, processed_in)

        # Detect status change
        new_status = getattr(db_obj, "status", None)
        if new_status and str(new_status) != str(old_status):
            self._on_status_change(
                db_obj, str(old_status) if old_status else None, str(new_status)
            )

        db_obj = self._after_update(db_obj)

        # 记录审计日志
        self._log_audit(
            "UPDATE", db_obj, changes=processed_in.model_dump(exclude_unset=True)
        )

        return self._to_response(db_obj)

    def delete(
        self,
        object_id: int,
        *,
        soft_delete: Optional[bool] = None,
    ) -> bool:
        exists = self.repository.exists(object_id)
        if not exists:
            raise_not_found(self.resource_name, object_id)

        self._before_delete(object_id)
        use_soft_delete = soft_delete
        if use_soft_delete is None:
            use_soft_delete = bool(self.soft_delete_field)
        deleted = self.repository.delete(object_id, soft_delete=use_soft_delete)
        if deleted:
            # 记录审计日志
            try:
                # 尝试获取对象ID，由于可能已经软删除，这里直接存ID
                self._log_audit("DELETE", object_id=object_id)
            except Exception:
                pass
            self._after_delete(object_id)
        return deleted

    def bulk_delete(
        self,
        ids: Sequence[int],
        *,
        soft_delete: Optional[bool] = None,
    ) -> int:
        deleted = 0
        for object_id in ids:
            if self.delete(object_id, soft_delete=soft_delete):
                deleted += 1
        return deleted

    # --------------------------------------------------------------------- #
    # Hooks (override in subclasses)
    # --------------------------------------------------------------------- #
    def _to_response(self, obj: ModelType) -> ResponseSchemaType:
        if not self.response_schema:
            raise NotImplementedError("response_schema is required for BaseCRUDService")
        return self.response_schema.model_validate(obj)

    def _before_create(self, obj_in: CreateSchemaType) -> CreateSchemaType:
        return obj_in

    def _after_create(self, db_obj: ModelType) -> ModelType:
        return db_obj

    def _before_update(
        self,
        object_id: int,
        obj_in: UpdateSchemaType,
        db_obj: ModelType,
    ) -> UpdateSchemaType:
        return obj_in

    def _after_update(self, db_obj: ModelType) -> ModelType:
        return db_obj

    def _before_delete(self, object_id: int) -> None:
        return None

    def _after_delete(self, object_id: int) -> None:
        return None

    def _on_status_change(
        self,
        db_obj: ModelType,
        from_status: Optional[str],
        to_status: str,
    ) -> None:
        """
        Hook called when an object's status changes.
        """
        from app.common.workflow.engine import workflow_engine

        workflow_engine.trigger(self.db, db_obj, from_status, to_status)

    def _before_list(self, params: QueryParams) -> QueryParams:
        return params

    def _after_list(
        self,
        result: PaginatedResult[ResponseSchemaType],
        params: QueryParams,
    ) -> PaginatedResult[ResponseSchemaType]:
        return result

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _merge_filters(
        self,
        params: QueryParams,
        extra_filters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        filters = dict(self._default_filters)
        filters.update(params.filters or {})
        if extra_filters:
            filters.update(extra_filters)

        if self.soft_delete_field and not params.include_deleted:
            filters.setdefault(self.soft_delete_field, {"is_null": True})

        if self.allowed_filter_fields:
            allowed = set(self.allowed_filter_fields)
            filters = {k: v for k, v in filters.items() if k in allowed}

        return filters

    def _resolve_sorting(self, params: QueryParams) -> Tuple[Optional[str], SortOrder]:
        field = params.sort_by or self.default_sort_field
        order = params.sort_order or self.default_sort_order

        if self.allowed_sort_fields and field and field not in self.allowed_sort_fields:
            field = self.default_sort_field

        return field, order

    def _ensure_unique(
        self,
        unique_fields: UniqueCheckType,
        *,
        data: Optional[BaseModel] = None,
        current_id: Optional[int] = None,
    ) -> None:
        if not unique_fields:
            return

        payload: Dict[str, Any] = {}
        if isinstance(unique_fields, dict):
            payload = dict(unique_fields)
        elif isinstance(unique_fields, str):
            if not data:
                raise ValueError(
                    "data is required when unique fields are provided as names"
                )
            payload = {unique_fields: getattr(data, unique_fields)}
        elif isinstance(unique_fields, (list, tuple, set)):
            if not data:
                raise ValueError(
                    "data is required when unique fields are provided as names"
                )
            payload = {field: getattr(data, field) for field in unique_fields}

        for field, value in payload.items():
            existing = self.repository.get_by_field(field, value)
            if existing and getattr(existing, "id", None) != current_id:
                raise_already_exists(self.resource_name, field, str(value))

    def _log_audit(
        self,
        action_type: str,
        db_obj: Optional[ModelType] = None,
        object_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        自动记录审计日志
        """
        try:
            from app.common.context import get_audit_context
            from app.services.permission_audit_service import PermissionAuditService

            ctx = get_audit_context()
            operator_id = ctx.get("operator_id")

            # 如果没有操作人ID（例如后台任务），不记录或记录为系统操作
            if not operator_id:
                return

            target_id = object_id or getattr(db_obj, "id", None)
            if not target_id:
                return

            # 构建 action 字符串，例如 MATERIAL_CREATE
            model_name = self.model.__name__
            resource_prefix = model_name.upper()
            action = f"{resource_prefix}_{action_type}"

            # 构建详情
            detail = ctx.get("detail") or {}
            if changes:
                detail["changes"] = changes

            if not detail.get("description"):
                detail["description"] = (
                    f"{self.resource_name} {action_type.lower()}: {target_id}"
                )

            PermissionAuditService.log_audit(
                db=self.db,
                operator_id=operator_id,
                action=action,
                target_type=model_name.lower(),
                target_id=target_id,
                detail=detail,
                ip_address=ctx.get("client_ip"),
                user_agent=ctx.get("user_agent"),
            )
        except Exception as e:
            # 审计日志记录失败不应阻断主业务逻辑
            import logging

            logging.getLogger(__name__).warning(f"Failed to record audit log: {e}")
