# 通用时间范围工具使用说明

统一月初/月末、当月/上月、按年月取范围等计算，替代手写 `replace(day=1)`、`date(year, month+1, 1) - timedelta(days=1)` 的重复代码。

## 1. 提供的函数（`app.common.date_range`）

| 函数 | 说明 | 示例 |
|------|------|------|
| `get_month_range(d)` | 指定日期所在月的 (月初, 月末) | `get_month_range(date.today())` → (本月1号, 本月最后一天) |
| `get_last_month_range(d)` | 指定日期所在月的上个月的 (月初, 月末) | `get_last_month_range(date.today())` |
| `get_month_range_by_ym(year, month)` | 按年、月(1–12) 取该月 (月初, 月末) | `get_month_range_by_ym(2025, 1)` |
| `get_week_range(d)` | 指定日期所在周的 (周一, 周日) | `get_week_range(date.today())` |
| `month_start(d)` | 指定日期所在月的第一天 | `month_start(date.today())` |
| `month_end(d)` | 指定日期所在月的最后一天 | `month_end(date.today())` |

## 2. 迁移步骤

**改前：**
```python
today = date.today()
month_start = today.replace(day=1)
# 或
month_start = date(today.year, today.month, 1)
if today.month == 12:
    month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
else:
    month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
```

**改后：**
```python
from app.common.date_range import get_month_range, get_month_range_by_ym

today = date.today()
month_start, month_end = get_month_range(today)
# 若已有 year, month (1–12)：
month_start, month_end = get_month_range_by_ym(year, month_num)
```

**上月范围：**
```python
from app.common.date_range import get_last_month_range
last_month_start, last_month_end = get_last_month_range(date.today())
```

## 3. 已迁移文件示例

- `app/api/v1/endpoints/dashboard_stats.py` — 当月/上月/周范围
- `app/api/v1/endpoints/production/dashboard.py` — 本月月初
- `app/api/v1/endpoints/hr_management/dashboard.py` — 本月月初
- `app/api/v1/endpoints/materials/statistics.py` — 本月月初
- `app/api/v1/endpoints/business_support/dashboard.py` — 按年月取范围
- `app/services/project/resource_service.py` — 月份归一化（当月、月初、月末）
- `app/services/report_framework/adapters/sales.py` — 按年月取范围

## 4. 如何查找待迁移代码

在 `app/` 下搜索：`replace(day=1)`、`date(.*\.year.*\.month.*1)`、`month_start`、`month_end`、`timedelta(days=1)` 与月份边界计算。
