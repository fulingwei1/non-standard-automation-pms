# -*- coding: utf-8 -*-
"""
Shared CRUD helper types.

These types allow services to share the same pagination/query contract so
controllers no longer have to reinvent keyword/filters handling.
"""

from __future__ import annotations

from enum import Enum
from math import ceil
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator


class SortOrder(str, Enum):
    """Supported sort orders for list queries."""

    ASC = "asc"
    DESC = "desc"


class QueryParams(BaseModel):
    """
    Normalized query params that every CRUD list endpoint can reuse.

    Pagination is page-based to align with current API responses. Filters/search
    can be passed as dictionaries to keep controllers thin.
    """

    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(
        default=20, ge=1, le=200, description="Items per page (max 200)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Structured filter definition"
    )
    search: Optional[str] = Field(default=None, description="Free text keyword")
    search_fields: Optional[List[str]] = Field(
        default=None, description="Override search fields for this request"
    )
    sort_by: Optional[str] = Field(
        default=None, description="Sort field, falls back to service defaults"
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC, description="Sort order (asc/desc)"
    )
    load_relationships: Optional[List[str]] = Field(
        default=None, description="Relationships to eager load"
    )
    include_deleted: bool = Field(
        default=False,
        description="Whether to include soft-deleted records where supported",
    )

    @property
    def skip(self) -> int:
        """Translate page/page_size into an SQL offset."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Convenience limit alias."""
        return self.page_size

    def merged_filters(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Combine request filters with service-provided filters.

        The original filters dict is not mutated to keep the model immutable.
        """
        merged: Dict[str, Any] = {}
        if self.filters:
            merged.update(self.filters)
        if extra:
            merged.update(extra)
        return merged

    @field_validator("sort_order", mode="before")
    def _normalize_sort_order(cls, value: Any) -> SortOrder:
        """Accept mixed-case strings while keeping enum type internally."""
        if isinstance(value, SortOrder):
            return value
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ("asc", "desc"):
                return SortOrder(value_lower)
        raise ValueError("sort_order must be 'asc' or 'desc'")


T = TypeVar("T")


class PaginatedResult(BaseModel, Generic[T]):
    """Generic pagination container returned by services."""

    items: List[T] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)

    @property
    def pages(self) -> int:
        """Total number of pages."""
        if self.page_size <= 0:
            return 0
        return int(ceil(self.total / self.page_size))

    def to_dict(self) -> Dict[str, Any]:
        """Drop-in helper for legacy dict responses."""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "pages": self.pages,
        }
