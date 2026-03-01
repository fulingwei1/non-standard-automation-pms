# 非标自动化项目管理系统测试修复报告

日期：2026-03-01
执行范围：后端健康检查、登录链路、数据库结构、API 路由扫描、核心单元测试

## 1) 诊断结果

- `/health` 正常（200）
- 登录接口最初 500：根因是 SQLite 数据库结构不完整（缺失关键表）
- 路由初始化阶段曾存在多个导入/加载问题（销售模块循环导入、AI 服务导入错误、权限依赖缺失）
- 全量 GET（无路径参数）路由扫描初始存在 5 个 500，后续回归又发现 3 个 500

## 2) 修复内容

### 2.1 已修复的关键问题

1. 登录 500（数据库缺表）
   - 重写 `scripts/init_db.py`，支持：重建 DB、创建模型表、执行 sqlite 迁移、初始化默认账号
   - 当前 DB 表数量：508；关键表 `users/roles/user_roles/login_attempts/employees/api_permissions` 均存在

2. `assembly_kit_service` 导入/函数缺失
   - 在 `app/services/assembly_kit_service.py` 补齐并导出端点依赖函数
   - 兼容现有单测 mock 行为

3. AI 服务导入错误
   - `app/services/schedule_generation_service.py` 去除无效导入 `avg`

4. 销售模块循环导入
   - `app/api/v1/endpoints/sales/__init__.py` 修正导入路径

5. 剩余 500（第一批）
   - `app/api/v1/endpoints/production/capacity/analysis.py`：SQLAlchemy `case` 语法兼容 SQLAlchemy 2.x
   - `app/api/v1/endpoints/sales/payments/payment_exports.py`：导出文件名 header 改为 RFC5987 编码
   - `app/api/v1/endpoints/sales/workflows.py`：补齐 `approver_type` 响应映射并修复 steps 更新逻辑
   - `app/api/v1/endpoints/sales_funnel_optimization.py`：`null` -> `None`
   - `app/api/v1/endpoints/timesheet/workflow.py`：兼容 list/dict 两种 service 返回结构

6. 路由扫描新增发现 500（第二批）
   - `app/models/base.py`：运行时 SQLite schema 补丁增加 `engineer_dimension_config` 缺失字段
   - `app/api/v1/presale_ai_win_rate.py`：模型准确度 fallback 返回字段与 schema 对齐（`average_error/last_updated`）

7. 全局导出兼容
   - `app/services/excel_export_service.py`：统一导出响应 header 支持 UTF-8 文件名与 ASCII fallback

## 3) 验证结果

### 3.1 核心 API 回归

- `/health` -> 200
- `POST /api/v1/auth/login` -> 200
- `GET /api/v1/auth/me` -> 200
- `GET /api/v1/roles/` -> 200
- `GET /api/v1/users/` -> 200
- `GET /api/v1/projects` -> 200
- `GET /api/v1/dashboard/stats` -> 200
- 修复目标接口全部 200：
  - `/api/v1/production/capacity/bottlenecks`
  - `/api/v1/sales/payments/invoices/export`
  - `/api/v1/sales/approval-workflows`
  - `/api/v1/sales/funnel/funnel/health-dashboard`
  - `/api/v1/timesheet/workflow/pending-tasks`
  - `/api/v1/engineer-performance/config/pending-approvals`
  - `/api/v1/engineer-performance/config/weights`
  - `/api/v1/presale/ai/model-accuracy`

### 3.2 路由扫描结果（GET + 无路径参数）

- 扫描总数：707
- 状态分布：
  - 200: 260
  - 400: 1
  - 404: 12
  - 422: 26
  - 429: 408
  - 500: 0

说明：429 为限流策略触发，不属于业务逻辑异常。

### 3.3 单元测试

执行：
`PYTHONPATH=. .venv/bin/pytest --no-cov tests/services/test_assembly_kit_service.py tests/unit/test_assembly_kit_service.py tests/unit/test_auth.py -q`

结果：
- 56 passed
- 1 warning（Pydantic `model_version` protected namespace）

## 4) 遗留问题

1. 非 500 错误仍存在（400/404/422）
   - 多数是接口预期行为（参数缺失、资源不存在、业务前置条件不满足）
   - 需按业务优先级逐项评估是否要改为更友好提示

2. 限流影响自动化扫描（大量 429）
   - 建议引入测试环境专用限流策略或白名单

3. SQLite 兼容补丁属于“运行时兜底”
   - 长期建议补齐正式迁移脚本，避免依赖运行时 ALTER

## 5) 下一步建议

1. 建立“核心链路回归脚本”（登录/鉴权/导出/审批/看板）并纳入 CI
2. 拆分并标记“必须 200”的接口清单，单独监控 5xx 与 P95 延迟
3. 对历史 sqlite 迁移进行一次基线清理，统一 schema 与 ORM
4. 补充 engineer-performance 与 presale-ai 的接口级测试用例，防止字段回归
