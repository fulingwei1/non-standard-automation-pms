# 通用模式问题分析 (#54-#61)

## ✅ #54 工具函数碎片化
**状态**: 已解决  
`app/utils/common.py` 已统一 clean_str/clean_name/clean_phone/clean_decimal/parse_date 等函数。  
新增 `app/utils/__init__.py` 提供统一 re-export 入口。

## ✅ #55 树形结构构建
**状态**: 已解决  
- 核心实现: `app/common/tree_builder.py`
- Re-export: `app/utils/tree.py` → `from app.utils.tree import build_tree`

## ✅ #56 文件上传
**状态**: 已解决  
`app/services/file_upload_service.py` 提供统一的 FileUploadService，含文件类型验证、大小限制、用户配额管理。

## ✅ #57 时间范围筛选
**状态**: 已解决  
- `app/common/date_range.py`: get_month_range / get_last_month_range / get_month_range_by_ym 等
- `app/services/statistics/base.py`: SyncStatisticsService 提供 count_by_field + 日期过滤基类
- 已通过 `app/utils/__init__.py` re-export date_range 函数

## ⚠️ #58 查询模式 (is_active)
**状态**: 框架级别，不适合简单合并  
`is_active` 字段广泛存在于 15+ 模型中，各自语义略有不同（Boolean vs Integer）。  
已有通用查询基础设施:
- `app/common/crud/filters.py`: QueryBuilder 通用过滤
- `app/common/crud/sync_filters.py`: 同步版本
- `app/common/query_filters.py`: 关键词搜索过滤

建议: 各服务按需在查询中添加 `.filter(Model.is_active == True)` 即可，无需额外抽象。

## ⚠️ #60 评论/跟进功能
**状态**: 各模块独立实现，结构相似但领域不同  
发现的实现:
- `TaskComment` (task_center) — 任务评论，含类型枚举
- `LeadFollowUp` (sales/leads) — 销售线索跟进
- `IssueFollowUp` (acceptance) — 验收问题跟进
- `ArrivalFollowUp` (shortage/arrivals) — 到货跟进

这些模型字段相似（content, creator, timestamp）但关联的业务实体不同。  
建议: 可考虑 Mixin 模式 (CommentMixin) 统一基础字段，但因各表已稳定运行，ROI 较低。标记为"可选优化"。

## ⚠️ #61 版本控制/历史记录
**状态**: 基础审计已有，完整版本控制待评估  
- `app/middleware/audit.py`: AuditMiddleware 捕获请求 IP/UA
- `app/common/context.py`: 审计上下文管理

完整的字段级变更历史（changelog）尚未实现。  
建议: 如需实现，推荐使用 SQLAlchemy-Continuum 或自建 `audit_log` 表 + event listener，属于框架级改造。
