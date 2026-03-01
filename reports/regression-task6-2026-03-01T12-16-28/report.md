# 任务6/8 回归测试报告

- 执行时间: 2026/3/1 20:16:28
- 目标环境: http://127.0.0.1:5173
- 覆盖范围: 销售模块 14 页 + 项目管理 6 页 + 售前模块 5 页（共 25 页）
- 执行方式: Playwright 自动化烟雾回归（页面可达性 + 前端异常 + API异常监测）

## 总览

- 总页面: **25**
- PASS: **0**
- WARN: **0**
- FAIL: **25**

## 模块统计

| 模块 | 计划页数 | 执行页数 | PASS | WARN | FAIL | 平均耗时 |
| --- | --- | --- | --- | --- | --- | --- |
| 销售模块 | 14 | 14 | 0 | 0 | 14 | 1ms |
| 项目管理 | 6 | 6 | 0 | 0 | 6 | 2ms |
| 售前模块 | 5 | 5 | 0 | 0 | 5 | 1ms |

## 页面明细

| 模块 | 页面 | 路由 | 结果 | 耗时 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 销售模块 | 销售目标 | `/sales/targets` | FAIL | 3ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 线索管理 | `/sales/leads` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 销售漏斗 | `/sales/funnel` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 销售分析 | `/sales/sales-analysis` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 商机管理 | `/sales/opportunities` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 客户管理 | `/sales/customers` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | AI销售助手 | `/sales/ai-assistant` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 智能报价 | `/sales/intelligent-quote` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 客户360 | `/sales/customer-360` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 销售自动化 | `/sales/automation` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 绩效与激励 | `/sales/performance-incentive` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 销售协同 | `/sales/collaboration` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 赢单率预测 | `/sales/win-rate-prediction` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 销售模块 | 竞争对手分析 | `/sales/competitor-analysis` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 项目管理 | 项目列表 | `/projects` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 项目管理 | 项目看板 | `/board` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 项目管理 | AI智能排计划入口 | `/schedule-generation` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 项目管理 | 工程师调度入口 | `/engineer-recommendation` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 项目管理 | 甘特依赖视图 | `/gantt` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 项目管理 | 资源全景 | `/resource-overview` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 售前模块 | 售前工作台 | `/presales-dashboard` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 售前模块 | 售前经理工作台 | `/presales-manager-dashboard` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 售前模块 | 方案评审 | `/presales-tasks` | FAIL | 1ms | 导航失败/超时；出现 1 条 pageerror |
| 售前模块 | 方案管理 | `/solutions` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |
| 售前模块 | 售前模板库 | `/presales/templates` | FAIL | 2ms | 导航失败/超时；出现 1 条 pageerror |

## 高频 API 异常

无 API 异常。

## 产物清单

- JSON原始报告: `report.json`
- 页面截图目录: `screenshots/`

> 说明：本次回归采用测试会话注入（demo_token + admin角色）保证可稳定访问受保护路由。
