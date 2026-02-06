# app.common Package
# 通用工具模块，包含跨模块共享的基础类和工具函数。
#
# ## 目录结构
#
# - `pagination.py` - 分页参数与 FastAPI 依赖（替代手写 offset = (page-1)*page_size）
# - `query_filters.py` - 关键词模糊搜索与分页应用（替代手写 .like / .offset /.limit）
# - `crud/` - CRUD 基类与查询构建器
#

from app.common.date_range import (
    get_month_range,
    get_last_month_range,
    get_month_range_by_ym,
    get_week_range,
    month_start,
    month_end,
)
from app.common.pagination import (
    PaginationParams,
    get_pagination_params,
    get_pagination_query,
    paginate_list,
)
from app.common.query_filters import apply_keyword_filter, apply_pagination

__all__ = [
    # 时间范围
    "get_month_range",
    "get_last_month_range",
    "get_month_range_by_ym",
    "get_week_range",
    "month_start",
    "month_end",
    # 分页
    "PaginationParams",
    "get_pagination_params",
    "get_pagination_query",
    "paginate_list",
    "apply_keyword_filter",
    "apply_pagination",
]
