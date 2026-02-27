# 报表统计服务整合方案

> Issue #27: 报表统计服务分散  
> Issue #41: 统计服务重复  
> Branch: `fix/stats-reports-v2`

## 现有基础设施

### 统计基类
| 基类 | 路径 | 模式 |
|------|------|------|
| `SyncStatisticsService` | `app/services/statistics/base.py` | 同步 Session，count_by_field/count_by_status |
| `BaseStatisticsService` | `app/common/statistics/base.py` | AsyncSession，count_by_date_range/get_trend/get_distribution |
| `StatisticsAggregator` | `app/common/statistics/aggregator.py` | 组合多个统计服务结果 |

### 报表框架
| 框架 | 路径 | 说明 |
|------|------|------|
| `report_framework` | `app/services/report_framework/` | 完整框架：YAML配置 + 适配器 + 多格式渲染 |
| `BaseReportGenerator` | `app/common/reports/base.py` | 简单基类（被 report_framework 取代） |

## #41 已完成：统计服务重构

### 已迁移到 SyncStatisticsService
- ✅ `issue_statistics_service.py` — 新增 `IssueStatistics` 类，5个 count_by_field 调用替代手动逐值查询
- ✅ `project_statistics_service.py` — status/stage/health 统计改用 SQL GROUP BY；新增 `ProjectStatistics` 类

### 保持原样（业务逻辑过于特殊）
- `kit_rate_statistics_service.py` — 齐套率计算依赖 KitRateService，非简单聚合
- `payment_statistics_service.py` — 回款统计涉及 Decimal 精度、发票/合同关联查询
- `collaboration_rating/statistics.py` — 评价质量分析（标准差、维度分析），已有 class 结构

## #27 未迁移到 report_framework 的报表端点

以下端点直接在 API 层生成报表数据，未使用 `report_framework`：

1. `app/api/v1/endpoints/acceptance/reports.py`
2. `app/api/v1/endpoints/business_support_orders/contract_reports.py`
3. `app/api/v1/endpoints/business_support_orders/invoice_reports.py`
4. `app/api/v1/endpoints/business_support_orders/payment_reports.py`
5. `app/api/v1/endpoints/business_support_orders/reports.py`
6. `app/api/v1/endpoints/production/capacity/report.py`
7. `app/api/v1/endpoints/production/work_reports.py`
8. `app/api/v1/endpoints/report.py`
9. `app/api/v1/endpoints/shortage/handling/reports.py`
10. `app/api/v1/endpoints/timesheet/reports.py`

**已使用 report_framework 的端点：**
- `acceptance/report_generation.py`
- `business_support_orders/sales_reports.py`
- `management_rhythm/reports.py` / `reports_unified.py`
- `report_center/*`
- `timesheet/reports_unified.py`
- `_shared/unified_reports.py`

### 迁移建议
逐步为上述 10 个端点创建 `report_framework` 适配器，优先迁移有导出需求（PDF/Excel）的端点。纯 JSON API 端点优先级较低。
