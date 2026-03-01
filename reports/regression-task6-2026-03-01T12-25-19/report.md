# 任务6/8 回归测试报告

- 执行时间: 2026/3/1 20:25:19
- 目标环境: http://127.0.0.1:5173
- 覆盖范围: 销售模块 14 页 + 项目管理 6 页 + 售前模块 5 页（共 25 页）
- 执行方式: Playwright 自动化烟雾回归（页面可达性 + 前端异常 + API异常监测）

## 总览

- 总页面: **25**
- PASS: **9**
- WARN: **16**
- FAIL: **0**

## 模块统计

| 模块 | 计划页数 | 执行页数 | PASS | WARN | FAIL | 平均耗时 |
| --- | --- | --- | --- | --- | --- | --- |
| 销售模块 | 14 | 14 | 9 | 5 | 0 | 2475ms |
| 项目管理 | 6 | 6 | 0 | 6 | 0 | 2483ms |
| 售前模块 | 5 | 5 | 0 | 5 | 0 | 2451ms |

## 页面明细

| 模块 | 页面 | 路由 | 结果 | 耗时 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 销售模块 | 销售目标 | `/sales/targets` | WARN | 2512ms | 控制台错误 16 条；API异常 4 条 |
| 销售模块 | 线索管理 | `/sales/leads` | WARN | 2450ms | 控制台错误 16 条；API异常 4 条 |
| 销售模块 | 销售漏斗 | `/sales/funnel` | WARN | 2450ms | 控制台错误 20 条；API异常 8 条 |
| 销售模块 | 销售分析 | `/sales/sales-analysis` | PASS | 2443ms | 无 |
| 销售模块 | 商机管理 | `/sales/opportunities` | WARN | 2453ms | 控制台错误 20 条；API异常 6 条 |
| 销售模块 | 客户管理 | `/sales/customers` | WARN | 2454ms | 控制台错误 9 条；API异常 3 条 |
| 销售模块 | AI销售助手 | `/sales/ai-assistant` | PASS | 2457ms | 无 |
| 销售模块 | 智能报价 | `/sales/intelligent-quote` | PASS | 2453ms | 无 |
| 销售模块 | 客户360 | `/sales/customer-360` | PASS | 2482ms | 无 |
| 销售模块 | 销售自动化 | `/sales/automation` | PASS | 2472ms | 无 |
| 销售模块 | 绩效与激励 | `/sales/performance-incentive` | PASS | 2463ms | 无 |
| 销售模块 | 销售协同 | `/sales/collaboration` | PASS | 2453ms | 无 |
| 销售模块 | 赢单率预测 | `/sales/win-rate-prediction` | PASS | 2638ms | 无 |
| 销售模块 | 竞争对手分析 | `/sales/competitor-analysis` | PASS | 2476ms | 无 |
| 项目管理 | 项目列表 | `/projects` | WARN | 2491ms | 控制台错误 8 条；API异常 2 条 |
| 项目管理 | 项目看板 | `/board` | WARN | 2545ms | 控制台错误 16 条；API异常 4 条 |
| 项目管理 | AI智能排计划入口 | `/schedule-generation` | WARN | 2457ms | 控制台错误 6 条；API异常 2 条 |
| 项目管理 | 工程师调度入口 | `/engineer-recommendation` | WARN | 2493ms | 控制台错误 6 条；API异常 2 条 |
| 项目管理 | 甘特依赖视图 | `/gantt` | WARN | 2463ms | 控制台错误 8 条；API异常 2 条 |
| 项目管理 | 资源全景 | `/resource-overview` | WARN | 2450ms | 控制台错误 8 条；API异常 2 条 |
| 售前模块 | 售前工作台 | `/presales-dashboard` | WARN | 2458ms | 控制台错误 20 条；API异常 7 条 |
| 售前模块 | 售前经理工作台 | `/presales-manager-dashboard` | WARN | 2448ms | 控制台错误 20 条；API异常 7 条 |
| 售前模块 | 方案评审 | `/presales-tasks` | WARN | 2448ms | 控制台错误 8 条；API异常 2 条 |
| 售前模块 | 方案管理 | `/solutions` | WARN | 2445ms | 控制台错误 8 条；API异常 2 条 |
| 售前模块 | 售前模板库 | `/presales/templates` | WARN | 2457ms | 控制台错误 6 条；API异常 2 条 |

## 高频 API 异常

| API异常（聚合） | 出现次数 |
| --- | --- |
| GET /api/v1/projects/ -> 401 | 10 |
| GET /api/v1/customers/ -> 401 | 9 |
| GET /api/v1/sales/statistics/funnel -> 401 | 4 |
| GET /api/v1/users/ -> 401 | 4 |
| GET /api/v1/notifications/ -> 401 | 4 |
| GET /api/v1/dashboard/stats/sales -> 401 | 4 |
| GET /api/v1/node-tasks/my-tasks -> 401 | 4 |
| GET /api/v1/sales/targets -> 401 | 2 |
| GET /api/v1/sales/team -> 401 | 2 |
| GET /api/v1/sales/leads -> 401 | 2 |
| GET /api/v1/sales/opportunities -> 401 | 2 |
| GET /api/v1/projects/views/pipeline -> 401 | 2 |
| GET /api/v1/resource-overview/ -> 401 | 2 |
| GET /api/v1/dashboard/unified/SUPER_ADMIN -> 401 | 2 |
| GET /api/v1/presale/tickets -> 401 | 2 |
| GET /api/v1/presale/proposals/solutions -> 401 | 2 |
| GET /api/v1/presale/templates -> 401 | 2 |

## 产物清单

- JSON 原始报告: `report.json`
- 页面截图目录: `screenshots/`
- 报告目录: `regression-task6-2026-03-01T12-25-19`

> 备注：本次为页面级回归烟雾测试，使用测试会话注入保障可访问受保护路由。
