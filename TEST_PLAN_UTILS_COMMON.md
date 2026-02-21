# Utils 和 Common 层测试计划

## 目标
- Utils 层: 40-50个测试文件
- Common 层: 15-20个测试文件
- 总测试用例: 600-900个
- 覆盖率: >90%

## Utils 测试模块（优先级排序）

### 第一优先级（核心工具）
1. ✅ numerical_utils.py - 数值计算
2. ✅ risk_calculator.py - 风险计算
3. ✅ batch_operations.py - 批量操作
4. ⬜ cache_decorator.py - 缓存装饰器
5. ⬜ rate_limit_decorator.py - 限流装饰器
6. ⬜ db_helpers.py - 数据库辅助
7. ⬜ pagination.py - 分页工具

### 第二优先级（数据处理）
8. ⬜ domain_codes.py - 领域代码
9. ⬜ code_config.py - 代码配置
10. ⬜ spec_matcher.py - 规格匹配
11. ⬜ spec_match_service.py - 规格匹配服务
12. ⬜ permission_helpers.py - 权限辅助
13. ⬜ role_inheritance_utils.py - 角色继承

### 第三优先级（调度和任务）
14. ⬜ scheduler.py - 调度器
15. ⬜ scheduler_metrics.py - 调度指标
16. ⬜ scheduled_tasks.py - 定时任务
17. ⬜ alert_escalation_task.py - 告警升级

### 第四优先级（其他工具）
18. ⬜ redis_client.py - Redis客户端
19. ⬜ wechat_client.py - 微信客户端
20. ⬜ init_data.py - 初始化数据
21. ⬜ init_permissions_data.py - 权限初始化

## Common 测试模块

### 第一优先级
1. ⬜ query_filters.py - 查询过滤器
2. ⬜ date_range.py - 日期范围
3. ⬜ context.py - 上下文
4. ⬜ tree_builder.py - 树构建器
5. ⬜ pagination.py - 分页

### 第二优先级（CRUD）
6. ⬜ crud/base_crud_service.py - CRUD基类
7. ⬜ crud/service.py - 服务基类
8. ⬜ crud/sync_service.py - 同步服务
9. ⬜ crud/sync_repository.py - 同步仓库
10. ⬜ crud/sync_filters.py - 同步过滤

### 第三优先级（统计和报表）
11. ⬜ statistics/aggregator.py - 聚合器
12. ⬜ statistics/helpers.py - 统计辅助
13. ⬜ statistics/base.py - 统计基类
14. ⬜ dashboard/base.py - 仪表板基类
15. ⬜ reports/base.py - 报表基类

### 第四优先级（工作流）
16. ⬜ workflow/engine.py - 工作流引擎

## 测试策略
- 每个模块 10-20个测试用例
- 覆盖: 正常流程, 边界条件, 异常处理, 性能
- 使用 pytest fixtures
- Mock 外部依赖（数据库、Redis、微信等）
- 纯函数优先测试

## 进度跟踪
- 开始时间: 2026-02-21 21:40
- 预计完成: 2026-02-21 23:10
